from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import OmniBoundingVolume, LColor
from panda3d.core import PTAVecBase4f, Vec4F
from panda3d.core import Texture, GeomEnums

from ..shaders import OffsetScaleInstanceControl
from .. import settings

from random import random, uniform
from array import array
from itertools import chain
import sys

class TerrainObjectFactory(object):
    def __init__(self):
        pass

    def create_object(self):
        return None

class TerrainPopulatorBase(object):
    def __init__(self, objects_factory, count, placer):
        self.objects_factory = objects_factory
        self.count = count
        self.placer = placer
        self.max_instances = None
        self.object_template = None

    def generate_instances_info_for(self, patch):
        if callable(self.count):
            patch_count = self.count(patch)
        else:
            patch_count = self.count
        if self.max_instances is not None:
            patch_count = min(patch_count, self.max_instances)
        count = 0
        offsets = []
        while count < patch_count:
            offset = self.placer.place_new(count, patch)
            if offset is not None:
                offsets.append(offset)
            count += 1
        return offsets

    def create_object_template(self):
        if self.object_template is None:
            self.object_template = self.objects_factory.create_object()
            self.object_template.create_instance(self.create_object_template_instance_cb)

    def delete_object_template(self):
        if self.object_template is not None:
            self.object_template.remove_instance()
            self.object_template = None

    def create_object_template_instance_cb(self):
        pass

    def update_instance(self):
        if self.object_template is not None and self.object_template.instance_ready:
            self.object_template.update_instance()

class ShapeTerrainPopulatorBase(TerrainPopulatorBase):
    pass

class PatchedTerrainPopulatorBase(TerrainPopulatorBase):
    def __init__(self, objects_factory, count, placer):
        TerrainPopulatorBase.__init__(self, objects_factory, count, placer)
        self.objects_factory = objects_factory
        self.count = count
        self.placer = placer
        self.patch_map = {}
        self.lod_aware = False

    def do_create_patch_instances(self, patch, terrain_patch):
        pass

    def do_remove_patch_instances(self, patch, terrain_patch):
        pass

    def create_instance_patch(self, terrain_patch):
        self.create_object_template()
        if not terrain_patch in self.patch_map:
            data = self.generate_instances_info_for(terrain_patch)
            patch = TerrainPopulatorPatch(data)
            self.do_create_patch_instances(patch, terrain_patch)
            self.patch_map[terrain_patch] = patch

    def remove_instance_patch(self, terrain_patch):
        if terrain_patch in self.patch_map:
            patch = self.patch_map[terrain_patch]
            self.do_remove_patch_instances(patch, terrain_patch)
            del self.patch_map[terrain_patch]

class CpuTerrainPopulator(PatchedTerrainPopulatorBase):
    def __init__(self, objects_factory, count, max_instances, placer):
        PatchedTerrainPopulatorBase.__init__(self, objects_factory, count, placer)

    def create_object_template_instance_cb(self, terrain_object):
        #Hide the main instance
        terrain_object.instance.stash()

    def do_create_patch_instances(self, patch, terrain_patch):
        instances = []
        for (i, offset) in enumerate(patch.data):
            (x, y, height, scale) = offset
            #TODO: This should be created in create_instance and derived from the parent
            child = render.attach_new_node('instance_%d' % i)
            self.object_template.instance.instanceTo(child)
            child.set_pos(x, y, height)
            child.set_scale(scale)
            instances.append(child)
        patch.instances = instances

    def do_remove_patch_instances(self, patch, terrain_patch):
        for instance in patch.instances:
            instance.remove_node()
        patch.instances = []

class GpuTerrainPopulator(PatchedTerrainPopulatorBase):
    def __init__(self, objects_factory, count, max_instances, placer):
        PatchedTerrainPopulatorBase.__init__(self, objects_factory, count, placer)
        self.max_instances = max_instances
        self.rebuild = False

    def create_object_template_instance_cb(self, terrain_object):
        self.object_template.shader.set_instance_control(OffsetScaleInstanceControl(self.max_instances))
        bounds = OmniBoundingVolume()
        terrain_object.instance.node().setBounds(bounds)
        terrain_object.instance.node().setFinal(1)

    def do_create_patch_instances(self, patch, terrain_patch):
        self.rebuild = True

    def do_remove_patch_instances(self, patch, terrain_patch):
        self.rebuild = True

    def generate_table(self):
        data = []
        for patch in self.patch_map.values():
            data += patch.data
        offsets_nb = len(data)
        if settings.instancing_use_tex:
            offsets = data
        else:
            offsets = PTAVecBase4f.emptyArray(offsets_nb)
            for offset in data:
                    offsets[offsets_nb] = offset
        if settings.instancing_use_tex:
            texture = Texture()
            texture.setup_buffer_texture(len(offsets), Texture.T_float, Texture.F_rgba32, GeomEnums.UH_static)
            flattened_data = list(chain.from_iterable(offsets))
            data = array("f", flattened_data)
            if sys.version_info[0] < 3:
                texture.setRamImage(data.tostring())
            else:
                texture.setRamImage(data.tobytes())
            self.object_template.appearance.offsets = texture
        else:
            self.object_template.appearance.offsets = offsets
        self.object_template.instance.set_instance_count(offsets_nb)
        self.object_template.shader.apply(self.object_template.shape, self.object_template.appearance)
        self.rebuild = False

    def update_instance(self):
        if self.object_template is not None and self.object_template.instance_ready:
            if self.rebuild:
                self.generate_table()
            self.object_template.update_instance()

class MultiTerrainPopulator():
    def __init__(self, populators=None):
        if populators is None:
            populators = []
        self.populators =  populators
        self.lod_aware = False

    def add_populator(self, populator):
        self.populators.append(populator)

    def create_instance(self):
        for populator in self.populators:
            populator.create_instance()

    def create_instance_patch(self, patch):
        for populator in self.populators:
            populator.create_instance_patch(patch)

    def remove_instance_patch(self, patch):
        for populator in self.populators:
            populator.remove_instance_patch(patch)

    def update_instance(self):
        for populator in self.populators:
            populator.update_instance()

class TerrainPopulatorPatch(object):
    def __init__(self, data):
        self.data = data
        self.children = []

    def split(self):
        pass

    def merge(self):
        pass

class ObjectPlacer(object):
    def __init__(self):
        pass

    def place_new(self, count):
        return None

class RandomObjectPlacer(ObjectPlacer):
    def __init__(self, terrain):
        ObjectPlacer.__init__(self)
        self.terrain = terrain

    def place_new(self, count, patch=None):
        if patch is not None:
            u = random()
            v = random()
            height = self.terrain.get_height_patch(patch, u, v)
            x, y = patch.get_xy_for(u, v)
            x *= self.terrain.size
            y *= self.terrain.size
        else:
            x = uniform(-self.terrain.size, self.terrain.size)
            y = uniform(-self.terrain.size, self.terrain.size)
            height = self.terrain.get_height((x, y))
        #TODO: Should not have such explicit dependency
        if height > self.terrain.water.level:
            scale = uniform(0.1, 0.5)
            return (x, y, height, scale)
        else:
            return None
