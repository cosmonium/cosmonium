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

    def create_object(self):
        terrain_object = self.objects_factory.create_object()
        return terrain_object

    def create_object_instance_cb(self, terrain_object, patch):
        pass

    def create_object_instance(self, terrain_object, patch):
        terrain_object.create_instance(self.create_object_instance_cb, patch)

    def do_create_instances(self, terrain_object):
        pass

    def update_instance(self):
        pass

class ShapeTerrainPopulatorBase(TerrainPopulatorBase):
    def __init__(self, objects_factory, count, placer):
        TerrainPopulatorBase.__init__(self, objects_factory, count, placer)
        self.terrain_object = None

    def create_instance(self):
        if self.terrain_object is None:
            self.terrain_object = self.create_object()
        self.do_create_instances(self.terrain_object)

    def update_instance(self):
        if self.terrain_object is not None and self.terrain_object.instance_ready:
            self.terrain_object.update_instance()

class PatchedTerrainPopulatorBase(TerrainPopulatorBase):
    def __init__(self, objects_factory, count, placer):
        TerrainPopulatorBase.__init__(self, objects_factory, count, placer)
        self.objects_factory = objects_factory
        self.count = count
        self.placer = placer
        self.patch_map = {}
        self.lod_aware = False

    def create_instance_patch(self, patch):
        if not patch in self.patch_map:
            terrain_object = self.create_object()
            self.do_create_instances(terrain_object, patch)
            self.patch_map[patch] = terrain_object

    def remove_instance_patch(self, patch):
        if patch in self.patch_map:
            terrain_object = self.patch_map[patch]
            terrain_object.remove_instance()
            del self.patch_map[patch]

    def update_instance(self):
        for terrain_object in self.patch_map.values():
            if terrain_object.instance_ready:
                terrain_object.update_instance()

class CpuTerrainPopulator(PatchedTerrainPopulatorBase):
    def __init__(self, objects_factory, count, max_instances, placer):
        PatchedTerrainPopulatorBase.__init__(self, objects_factory, count, placer)

    def create_object_instance_cb(self, terrain_object, patch):
        #Hide the main instance
        terrain_object.instance.stash()
        if callable(self.count):
            patch_count = self.count(patch)
        else:
            patch_count = self.count
        count = 0
        while count < patch_count:
            offset = self.placer.place_new(count, patch)
            if offset is not None:
                (x, y, height, scale) = offset
                #TODO: This should be created in create_instance and derived from the parent
                child = render.attach_new_node('instance_%d' % count)
                terrain_object.instance.instanceTo(child)
                child.set_pos(x, y, height)
                child.set_scale(scale)
            count += 1

    def do_create_instances(self, terrain_object, patch):
        if terrain_object is None: return
        self.create_object_instance(terrain_object, (patch,))

class GpuTerrainPopulator(PatchedTerrainPopulatorBase):
    def __init__(self, objects_factory, count, max_instances, placer):
        PatchedTerrainPopulatorBase.__init__(self, objects_factory, count, placer)
        self.max_instances = max_instances

    def create_object(self):
        terrain_object = TerrainPopulatorBase.create_object(self)
        if terrain_object is not None:
            terrain_object.shader.set_instance_control(OffsetScaleInstanceControl(self.max_instances))
        return terrain_object

    def create_object_instance_cb(self, terrain_object, patch):
        bounds = OmniBoundingVolume()
        terrain_object.instance.node().setBounds(bounds)
        terrain_object.instance.node().setFinal(1)
        terrain_object.instance.set_instance_count(self.offsets_nb)

    def do_create_instances(self, terrain_object, patch):
        if terrain_object is None: return
        if callable(self.count):
            patch_count = self.count(patch)
        else:
            patch_count = self.count
        patch_count = min(patch_count, self.max_instances)
        if settings.instancing_use_tex:
            offsets = []
        else:
            offsets = PTAVecBase4f.emptyArray(patch_count)
        self.offsets_nb = 0
        while self.offsets_nb < patch_count:
            offset = self.placer.place_new(self.offsets_nb, patch)
            if offset is not None:
                if settings.instancing_use_tex:
                    offsets.append(offset)
                else:
                    offsets[self.offsets_nb] = offset
            self.offsets_nb += 1
        if settings.instancing_use_tex:
            texture = Texture()
            texture.setup_buffer_texture(len(offsets), Texture.T_float, Texture.F_rgba32, GeomEnums.UH_static)
            flattened_data = list(chain.from_iterable(offsets))
            data = array("f", flattened_data)
            if sys.version_info[0] < 3:
                texture.setRamImage(data.tostring())
            else:
                texture.setRamImage(data.tobytes())
            terrain_object.appearance.offsets = texture
        else:
            terrain_object.appearance.offsets = offsets
        self.create_object_instance(terrain_object, (patch,))

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
    def __init__(self):
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
