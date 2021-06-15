#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2019 Laurent Deru.
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


from direct.task.Task import gather

from ..appearances import AppearanceBase, Appearance, TexturesBlock
from ..textures import TextureArray
from ..astro import units
from ..dircontext import defaultDirContext
from .. import settings

from .shaders import TextureDictionaryDataSource, DetailMap

from math import pi

class TexturesDictionary(AppearanceBase):
    def __init__(self, textures, scale_factor=(1.0, 1.0), tiling=None, srgb=None, array=True, context=defaultDirContext):
        AppearanceBase.__init__(self)
        self.scale_factor = scale_factor
        self.tiling = tiling
        if srgb is None:
            srgb = settings.srgb
        self.srgb = srgb
        self.nb_textures = 0
        self.nb_blocks = 0
        self.nb_arrays = 0
        self.extend = 2 * pi * max(self.scale_factor) * units.m
        self.resolved = False
        self.loaded = False
        self.task = None
        self.blocks = {}
        self.blocks_index = {}
        if settings.use_texture_array and array:
            self.texture_array = True
        else:
            self.texture_array = True
        self.textures = []
        self.texture_categories = {}
        for (name, entry) in textures.items():
            if not isinstance(entry, TexturesBlock):
                albedo = entry
                entry = TexturesBlock()
                entry.set_albedo(albedo, context)
            self.blocks[name] = entry
            self.blocks_index[name] = self.nb_blocks
            self.textures += entry.textures
            if not self.texture_array:
                entry.set_target(False, "tex_" + name)
            self.nb_textures += entry.nb_textures
            self.nb_blocks += 1
        if self.texture_array:
            self.texture_arrays = {}
        for texture in self.textures:
            if self.texture_array:
                if texture.category not in self.texture_arrays:
                    self.texture_arrays[texture.category] = TextureArray(srgb=texture.srgb)
                    self.texture_arrays[texture.category].set_target(False, "tex_array_%s" % texture.category)
                    self.nb_arrays += 1
                self.texture_arrays[texture.category].add_texture(texture)
            self.texture_categories[texture.category] = True

    def get_tex_id_for(self, block_id, category):
        block = self.blocks[block_id]
        texture = block.textures_map[category]
        return texture.array_id

    def apply_textures(self, instance):
        if self.texture_array:
            for texture in self.texture_arrays.values():
                texture.apply(instance)
        else:
            for entry in self.blocks.values():
                for texture in entry.textures:
                    texture.apply(instance)

    def load_textures(self, tasks_tree, shape, owner):
        tasks = []
        for entry in self.blocks.values():
            for texture in entry.textures:
                tasks.append(texture.load(tasks_tree, shape))
        return gather(*tasks)

    def load_texture_array(self, tasks_tree, shape, owner):
        tasks = []
        for texture in self.texture_arrays.values():
            tasks.append(texture.load(tasks_tree, shape))
        return gather(*tasks)

    def task_done(self, task):
        self.task = None

    async def load(self, tasks_tree, shape, owner):
        if not self.loaded:
            if self.task is None:
                if self.texture_array:
                    self.task = self.load_texture_array(tasks_tree, shape, owner)
                else:
                    self.task = self.load_textures(tasks_tree, shape, owner)
                self.task.setUponDeath(self.task_done)
            await self.task
            #TODO: loaded should be protected by a lock to avoid race condition with clear()
            self.loaded = True

    def apply(self, shape, instance):
        if not self.loaded:
            print("ERROR: Applying not loaded texture")
        self.apply_textures(instance)
        instance.set_shader_input("detail_factor", self.scale_factor)

    def clear_textures(self):
        for entry in self.blocks.values():
            for texture in entry.textures:
                texture.clear_all()

    def clear_texture_array(self):
        for texture in self.texture_arrays.values():
            texture.clear_all()

    def clear_all(self):
        if self.texture_array:
            self.clear_texture_array()
        else:
            self.clear_textures()
        self.loaded = False

    def update_lod(self, shape, apparent_radius, distance_to_obs, pixel_size):
        AppearanceBase.update_lod(self, shape, apparent_radius, distance_to_obs, pixel_size)
        height_under = shape.owner.anchor._height_under
        distance = distance_to_obs - height_under
        if distance > 0.0:
            size = self.extend / (distance * pixel_size)
            resolved = size > 1.0
            if resolved != self.resolved:
                self.resolved = resolved
                #TODO: this should be done properly
                shape.parent.shader.appearance.set_resolved(resolved)
                shape.parent.update_shader()

class ProceduralAppearance(AppearanceBase):
    def __init__(self, texture_control, texture_source, heightmap):
        AppearanceBase.__init__(self)
        self.texture_control = texture_control
        self.texture_source = texture_source
        self.appearance_source = TextureDictionaryDataSource(texture_source)
        self.shader_appearance = DetailMap(texture_control, heightmap, create_normals=True)

    def get_data_source(self):
        return self.appearance_source

    def get_shader_appearance(self):
        return self.shader_appearance

    async def load(self, tasks_tree, shape, owner):
        await self.texture_source.load(tasks_tree, shape, owner)

    def apply(self, shape, instance):
        self.texture_source.apply(shape, instance)

    def clear_patch(self, patch):
        self.texture_source.clear_patch(patch)

    def clear_all(self):
        self.texture_source.clear_all()

    def update_lod(self, shape, apparent_radius, distance_to_obs, pixel_size):
        self.texture_source.update_lod(shape, apparent_radius, distance_to_obs, pixel_size)
