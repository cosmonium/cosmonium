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

from __future__ import print_function
from __future__ import absolute_import

from ..appearances import AppearanceBase, Appearance, TexturesBlock
from ..textures import TextureArray
from ..astro import units
from ..dircontext import defaultDirContext

from .. import settings

from math import pi

class TextureTilingMode(object):
    F_none = 0
    F_hash = 1

class TexturesDictionary(AppearanceBase):
    def __init__(self, textures, scale_factor=(1.0, 1.0), tiling=TextureTilingMode.F_none, srgb=None, array=True, context=defaultDirContext):
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

    def apply_textures(self, shape):
        if self.texture_array:
            for texture in self.texture_arrays.values():
                texture.apply(shape)
        else:
            for entry in self.blocks.values():
                for texture in entry.textures:
                    texture.apply(shape)

    def texture_loaded_cb(self, texture, patch, owner):
        owner.jobs_done_cb(None)

    def load_textures(self, shape, owner):
        for entry in self.blocks.values():
            for texture in entry.textures:
                texture.load(shape, self.texture_loaded_cb, (shape, owner))

    def load_texture_array(self, shape, owner):
        for texture in self.texture_arrays.values():
            texture.load(shape, self.texture_loaded_cb, (shape, owner))

    def apply(self, shape, owner):
        if (shape.jobs & Appearance.JOB_TEXTURE_LOAD) == 0:
            #print("APPLY", shape, self.nb_textures)
            if self.nb_textures > 0:
                shape.jobs |= Appearance.JOB_TEXTURE_LOAD
                if self.texture_array:
                    shape.jobs_pending += self.nb_arrays
                    self.load_texture_array(shape, owner)
                else:
                    shape.jobs_pending += self.nb_textures
                    self.load_textures(shape, owner)

    def update_lod(self, shape, apparent_radius, distance_to_obs, pixel_size):
        AppearanceBase.update_lod(self, shape, apparent_radius, distance_to_obs, pixel_size)
        height_under = shape.owner.height_under
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
    def __init__(self,
                 scale_factor = (1, 1)):
        AppearanceBase.__init__(self)
        self.scale_factor = scale_factor
