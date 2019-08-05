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
    def __init__(self, object_template, count, placer):
        self.terrain = None
        self.object_template = object_template
        self.count = count
        self.placer = placer
        self.max_instances = None

    def set_parent(self, parent):
        self.parent = parent
        self.object_template.set_parent(parent)

    def set_owner(self, owner):
        self.owner = owner
        self.terrain = owner
        self.object_template.set_owner(owner)

    def add_after_effect(self, after_effect):
        self.object_template.add_after_effect(after_effect)

    def calc_nb_of_instances(self, patch):
        return self.count

    def generate_instances_info_for(self, patch):
        nb_of_instances = self.calc_nb_of_instances(patch)
        if self.max_instances is not None:
            nb_of_instances = min(nb_of_instances, self.max_instances)
        count = 0
        offsets = []
        while count < nb_of_instances:
            offset = self.placer.place_new(self.terrain, count, patch)
            if offset is not None:
                offsets.append(offset)
            count += 1
        return offsets

    def create_object_template(self):
        if self.object_template.instance is None:
            self.object_template.create_instance(self.create_object_template_instance_cb)

    def delete_object_template(self):
        if self.object_template.instance is not None:
            self.object_template.remove_instance()

    def create_object_template_instance_cb(self):
        pass

    def create_instance(self):
        pass

    def update_instance(self, camera_pos, orientation):
        if self.object_template.instance is not None and self.object_template.instance_ready:
            self.object_template.update_instance()

class ShapeTerrainPopulatorBase(TerrainPopulatorBase):
    pass

class PatchedTerrainPopulatorBase(TerrainPopulatorBase):
    def __init__(self, object_template, count, placer):
        TerrainPopulatorBase.__init__(self, object_template, count, placer)
        self.patch_map = {}
        self.visible_patches = {}
        self.lod_aware = False

    def calc_nb_of_instances(self, patch):
        scale = 1 << patch.lod
        count = self.count * self.terrain.size * self.terrain.size
        return round(count / scale)

    def create_data_for(self, patch, terrain_patch):
        data = self.generate_instances_info_for(terrain_patch)
        patch.set_data(data)

    def create_root_patch(self, terrain_patch):
        #print("CREATE", terrain_patch.str_id())
        if not terrain_patch in self.patch_map and terrain_patch.lod == 0:
            patch = TerrainPopulatorPatch(None)
            self.patch_map[terrain_patch] = patch

    def split_patch(self, terrain_patch):
        if not terrain_patch in self.patch_map: return
        #print("SPLIT", terrain_patch.str_id(), terrain_patch.x0, terrain_patch.y0, terrain_patch.x1, terrain_patch.y1)
        patch = self.patch_map[terrain_patch]
        if patch.data is None:
            self.create_data_for(patch, terrain_patch)
        bl = []
        br = []
        tr = []
        tl = []
        #TODO: Terrain scale should be retrieved properly...
        size = self.terrain.size
        for data in patch.data:
            (x, y, height, scale) = data
            (u, v) = terrain_patch.coord_to_uv((x / size, y / size))
            if u < 0.5:
                if v < 0.5:
                    tl.append(data)
                else:
                    bl.append(data)
            else:
                if v < 0.5:
                    tr.append(data)
                else:
                    br.append(data)
        #print(len(bl), len(br), len(tr), len(tl))
        self.patch_map[terrain_patch.children[0]] = TerrainPopulatorPatch(bl)
        self.patch_map[terrain_patch.children[1]] = TerrainPopulatorPatch(br)
        self.patch_map[terrain_patch.children[2]] = TerrainPopulatorPatch(tr)
        self.patch_map[terrain_patch.children[3]] = TerrainPopulatorPatch(tl)

    def merge_patch(self, terrain_patch):
        if not terrain_patch in self.patch_map: return
        #print("MERGE", terrain_patch.str_id())
        patch = self.patch_map[terrain_patch]
        for child in terrain_patch.children:
            if child in self.patch_map:
                del self.patch_map[child]
        patch.children = []

    def create_patch_instances(self, patch, terrain_patch):
        pass

    def show_patch(self, terrain_patch):
        self.create_object_template()
        #print("SHOW", terrain_patch.str_id())
        if terrain_patch in self.patch_map:
            patch = self.patch_map[terrain_patch]
            if patch.data is None:
                self.create_data_for(patch, terrain_patch)
            self.visible_patches[terrain_patch] = patch
            self.create_patch_instances(patch, terrain_patch)

    def remove_patch_instances(self, patch, terrain_patch):
        pass

    def hide_patch(self, terrain_patch):
        #print("HIDE", terrain_patch.str_id())
        if terrain_patch in self.visible_patches:
            patch = self.visible_patches[terrain_patch]
            self.remove_patch_instances(patch, terrain_patch)
            del self.visible_patches[terrain_patch]

class CpuTerrainPopulator(PatchedTerrainPopulatorBase):
    def __init__(self, object_template, count, max_instances, placer):
        PatchedTerrainPopulatorBase.__init__(self, object_template, count, placer)

    def create_object_template_instance_cb(self, terrain_object):
        #Hide the main instance
        terrain_object.instance.stash()

    def create_patch_instances(self, patch, terrain_patch):
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

    def remove_patch_instances(self, patch, terrain_patch):
        for instance in patch.instances:
            instance.remove_node()
        patch.instances = []

class GpuTerrainPopulator(PatchedTerrainPopulatorBase):
    def __init__(self, object_template, count, max_instances, placer):
        PatchedTerrainPopulatorBase.__init__(self, object_template, count, placer)
        self.max_instances = max_instances
        self.rebuild = False

    def create_object_template_instance_cb(self, terrain_object):
        self.object_template.shader.set_instance_control(OffsetScaleInstanceControl(self.max_instances))
        bounds = OmniBoundingVolume()
        terrain_object.instance.node().setBounds(bounds)
        terrain_object.instance.node().setFinal(1)

    def create_patch_instances(self, patch, terrain_patch):
        self.rebuild = True

    def remove_patch_instances(self, patch, terrain_patch):
        self.rebuild = True

    def generate_table(self):
        data = []
        for patch in self.visible_patches.values():
            data += patch.data
        offsets_nb = len(data)
        #print("GEN", offsets_nb)
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

    def update_instance(self, camera_pos, orientation):
        if self.object_template.instance is not None and self.object_template.instance_ready:
            if self.rebuild:
                self.generate_table()
            self.object_template.update_instance()

class MultiTerrainPopulator():
    def __init__(self, populators=None):
        if populators is None:
            populators = []
        self.populators =  populators
        self.lod_aware = False

    def set_parent(self, parent):
        for populator in self.populators:
            populator.set_parent(parent)

    def set_owner(self, owner):
        for populator in self.populators:
            populator.set_owner(owner)

    def add_after_effect(self, after_effect):
        for populator in self.populators:
            populator.add_after_effect(after_effect)

    def add_populator(self, populator):
        self.populators.append(populator)

    def create_root_patch(self, patch):
        for populator in self.populators:
            populator.create_root_patch(patch)

    def split_patch(self, patch):
        for populator in self.populators:
            populator.split_patch(patch)

    def merge_patch(self, patch):
        for populator in self.populators:
            populator.merge_patch(patch)

    def show_patch(self, patch):
        for populator in self.populators:
            populator.show_patch(patch)

    def hide_patch(self, patch):
        for populator in self.populators:
            populator.hide_patch(patch)

    def update_instance(self):
        for populator in self.populators:
            populator.update_instance()

class TerrainPopulatorPatch(object):
    def __init__(self, data=None):
        self.data = data

    def set_data(self, data):
        self.data = data

class ObjectPlacer(object):
    def __init__(self):
        pass

    def place_new(self, count):
        return None

class RandomObjectPlacer(ObjectPlacer):
    def place_new(self, terrain, count, patch=None):
        if patch is not None:
            u = random()
            v = random()
            height = terrain.get_height_patch(patch, u, v)
            x, y = patch.get_xy_for(u, v)
            x *= terrain.size
            y *= terrain.size
        else:
            x = uniform(-terrain.size, terrain.size)
            y = uniform(-terrain.size, terrain.size)
            height = terrain.get_height((x, y))
        #TODO: Should not have such explicit dependency
        if height > terrain.water.level:
            scale = uniform(0.1, 0.5)
            return (x, y, height, scale)
        else:
            return None
