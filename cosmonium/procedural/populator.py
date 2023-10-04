#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2023 Laurent Deru.
#
#Cosmonium is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Cosmonium is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#


from panda3d.core import OmniBoundingVolume
from panda3d.core import PTAVecBase4f
from panda3d.core import Texture, GeomEnums

from ..shaders.instancing import OffsetScaleInstanceControl
from ..datasource import DataSource
from ..foundation import VisibleObject
from .. import settings

from random import random, uniform
from array import array
from itertools import chain


class TerrainObjectFactory(object):
    def __init__(self):
        pass

    def create_object(self):
        return None


class TerrainPopulatorBase(VisibleObject):
    def __init__(self, object_template, count, placer):
        VisibleObject.__init__(self, None)
        self.terrain = None
        self.object_template = object_template
        self.count = count
        self.placer = placer
        self.max_instances = None
        self.task = None

    def is_flat(self):
        return True

    def set_parent(self, parent):
        VisibleObject.set_parent(self, parent)
        self.object_template.set_parent(parent)

    def set_owner(self, owner):
        VisibleObject.set_owner(self, owner)
        self.object_template.set_owner(owner)

    def set_body(self, body):
        self.object_template.set_body(body)

    def set_scene_anchor(self, scene_anchor):
        VisibleObject.set_scene_anchor(self, scene_anchor)
        self.object_template.set_scene_anchor(scene_anchor)

    def set_terrain(self, terrain):
        self.terrain = terrain

    def set_lights(self, lights):
        VisibleObject.set_lights(self, lights)
        self.object_template.set_lights(lights)

    def set_scattering(self, data_source, scattering_shader):
        self.object_template.set_scattering(data_source, scattering_shader)

    def add_source(self, source):
        self.object_template.add_source(source)

    def add_after_effect(self, after_effect):
        self.object_template.add_after_effect(after_effect)

    def calc_nb_of_instances(self, patch):
        return self.count

    def generate_object_instances_info_for(self, patch):
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

    async def create_object_template(self, scene_anchor):
        if self.object_template.instance is None:
            await self.object_template.create_instance(scene_anchor)
            self.configure_object_template()

    def delete_object_template(self):
        if self.object_template.instance is not None:
            self.object_template.remove_instance()

    def configure_object_template(self):
        pass

    def update(self, time, dt):
        self.object_template.update(time, dt)

    def task_done(self, task):
        self.task = None

    @property
    def shadows(self):
        return self.object_template.shadows

    def start_shadows_update(self):
        self.object_template.start_shadows_update()

    def end_shadows_update(self):
        self.object_template.end_shadows_update()

    #TODO: Temporarily stolen from foundation to be able to spawn task
    def check_and_create_instance(self):
        if not self.instance and not self.task:
            self.task = taskMgr.add(self.create_instance(), uponDeath=self.task_done)

    async def create_instance(self):
        await self.create_object_template(self.scene_anchor)
        self.instance = self.object_template.instance

    def update_instance(self, scene_manager, camera_pos, camera_rot):
        self.object_template.update_instance(scene_manager, camera_pos, camera_rot)

    def update_shader(self):
        if self.object_template.instance is not None and self.object_template.instance_ready:
            self.object_template.update_shader()

class ShapeTerrainPopulatorBase(TerrainPopulatorBase):
    pass

class PatchedTerrainPopulatorBase(TerrainPopulatorBase):
    def __init__(self, object_template, count, placer, min_lod=0):
        TerrainPopulatorBase.__init__(self, object_template, count, placer)
        self.min_lod = min_lod
        self.patch_map = {}
        self.visible_patches = {}

    def calc_nb_of_instances(self, patch):
        scale = 1 << patch.lod
        count = self.count * self.terrain.size * self.terrain.size
        scaled_count = count / (scale * scale)
        return scaled_count

    def patch_valid(self, terrain_patch):
        return terrain_patch in self.patch_map or terrain_patch.lod >= self.min_lod

    def create_patch_for(self, terrain_patch):
        patch = self.patch_map.get(terrain_patch)
        if patch is None and terrain_patch.lod >= self.min_lod:
            if settings.debug_lod_split_merge:
                print("Populator create patch", terrain_patch.str_id())
            patch = TerrainPopulatorPatch(None)
            self.patch_map[terrain_patch] = patch
        return patch

    def create_data_for(self, patch, terrain_patch):
        if settings.debug_lod_split_merge:
            print("Populator create data", terrain_patch.str_id())
        data = self.generate_object_instances_info_for(terrain_patch)
        patch.set_data(data)

    def create_root_patch(self, terrain_patch):
        if self.patch_valid(terrain_patch):
            self.create_patch_for(terrain_patch)

    def split_patch(self, terrain_patch):
        if not terrain_patch in self.patch_map: return
        if settings.debug_lod_split_merge:
            print("Populator split patch", terrain_patch.str_id())
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
                    bl.append(data)
                else:
                    tl.append(data)
            else:
                if v < 0.5:
                    br.append(data)
                else:
                    tr.append(data)
        #print(len(bl), len(br), len(tr), len(tl))
        self.patch_map[terrain_patch.children[0]] = TerrainPopulatorPatch(bl)
        self.patch_map[terrain_patch.children[1]] = TerrainPopulatorPatch(br)
        self.patch_map[terrain_patch.children[2]] = TerrainPopulatorPatch(tr)
        self.patch_map[terrain_patch.children[3]] = TerrainPopulatorPatch(tl)

    def merge_patch(self, terrain_patch):
        if not terrain_patch in self.patch_map: return
        if settings.debug_lod_split_merge:
            print("Populator merge patch", terrain_patch.str_id())
        patch = self.patch_map[terrain_patch]
        for child in terrain_patch.children:
            if child in self.patch_map:
                del self.patch_map[child]
        patch.children = []

    def create_object_instances(self, scene_anchor, patch, terrain_patch):
        pass

    def patch_done(self, terrain_patch, early):
        if terrain_patch in self.patch_map:
            patch = self.patch_map[terrain_patch]
            if patch.data is None:
                scene_anchor = self.owner.scene_anchor
                self.create_data_for(patch, terrain_patch)
                self.visible_patches[terrain_patch] = patch
                self.create_object_instances(scene_anchor, patch, terrain_patch)

    def create_patch_instance(self, terrain_patch):
        if not self.patch_valid(terrain_patch): return
        if settings.debug_lod_split_merge:
            print("Populator create patch instance", terrain_patch.str_id())
        patch = self.create_patch_for(terrain_patch)
        if patch is not None and patch.data is not None:
            scene_anchor = self.owner.scene_anchor
            self.visible_patches[terrain_patch] = patch
            self.create_object_instances(scene_anchor, patch, terrain_patch)

    def remove_object_instances(self, scene_anchor, patch, terrain_patch):
        pass

    def remove_patch_instance(self, terrain_patch):
        if settings.debug_lod_split_merge:
            print("Populator remove patch instance", terrain_patch.str_id())
        if terrain_patch in self.visible_patches:
            scene_anchor = self.owner.scene_anchor
            patch = self.visible_patches[terrain_patch]
            self.remove_object_instances(scene_anchor, patch, terrain_patch)
            del self.visible_patches[terrain_patch]

class CpuTerrainPopulator(PatchedTerrainPopulatorBase):
    def __init__(self, object_template, count, max_instances, placer, min_lod=0):
        PatchedTerrainPopulatorBase.__init__(self, object_template, count, placer, min_lod)

    def configure_object_template(self):
        #Hide the main instance
        self.object_template.instance.stash()

    def create_object_instances(self, scene_anchor, patch, terrain_patch):
        instances = []
        for (i, offset) in enumerate(patch.data):
            (x, y, height, scale) = offset
            child = scene_anchor.unshifted_instance.attach_new_node('instance_%d' % i)
            self.object_template.instance.instance_to(child)
            child.set_pos(x, y, height)
            child.set_scale(scale)
            instances.append(child)
        patch.instances = instances

    def remove_object_instances(self, scene_anchor, patch, terrain_patch):
        for instance in patch.instances:
            instance.remove_node()
        patch.instances = []

class OffsetsDataSource(DataSource):
    def __init__(self):
        DataSource.__init__(self, "offsets")
        self.offsets = None

    def set_offsets(self, offsets):
        self.offsets = offsets

    def apply(self, shape, instance):
        instance.set_shader_input('instances_offset', self.offsets)

class GpuTerrainPopulator(PatchedTerrainPopulatorBase):
    def __init__(self, object_template, count, max_instances, placer, min_lod=0):
        PatchedTerrainPopulatorBase.__init__(self, object_template, count, placer, min_lod)
        self.max_instances = max_instances
        self.object_template.shader.set_instance_control(OffsetScaleInstanceControl(self.max_instances))
        self.rebuild = False

    def configure_object_template(self):
        bounds = OmniBoundingVolume()
        self.object_template.instance.node().setBounds(bounds)
        self.object_template.instance.node().setFinal(1)
        self.object_template.add_source(OffsetsDataSource())
        self.generate_table()

    def create_object_instances(self, scene_anchor, patch, terrain_patch):
        self.rebuild = True

    def remove_object_instances(self, scene_anchor, patch, terrain_patch):
        self.rebuild = True

    def generate_table(self):
        data = []
        for patch in self.visible_patches.values():
            data += patch.data
        offsets_nb = len(data)
        if settings.debug_lod_split_merge:
            print("Populator regenerate", offsets_nb)
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
            texture.set_ram_image(data.tobytes())
            data_source = self.object_template.get_source('offsets')
            data_source.set_offsets(texture)
        else:
            data_source.set_offsets(offsets)
        self.object_template.instance.set_instance_count(offsets_nb)
        self.object_template.update_shader()
        self.rebuild = False

    def update_instance(self, scene_manager, camera_pos, camera_rot):
        self.object_template.update_instance(scene_manager, camera_pos, camera_rot)
        if self.object_template.instance is not None and self.object_template.instance_ready:
            if self.rebuild:
                self.generate_table()

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
        #TODO: Disabled for now
        if True or height > terrain.water.level:
            scale = uniform(0.1, 0.5)
            return (x, y, height, scale)
        else:
            return None
