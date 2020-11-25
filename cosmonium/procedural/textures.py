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

from panda3d.core import Texture

from ..textures import TextureSource
from .generator import GeneratorPool
from .shadernoise import NoiseShader
from .. import settings

class ProceduralVirtualTextureSource(TextureSource):
    tex_generators = {}
    cached = False
    procedural = True
    def __init__(self, noise, target, size):
        TextureSource.__init__(self)
        self.noise = noise
        self.target = target
        self.texture_size = size
        self.map_patch = {}

    def is_patched(self):
        return True

    def child_texture_name(self, patch):
        return None

    def texture_name(self, patch):
        return None

    def can_split(self, patch):
        return True

    def texture_loaded_cb(self, texture, patch, callback, cb_args):
        if texture is not None:
            self.map_patch[patch] = (texture, self.texture_size, patch.lod)
            if callback is not None:
                callback(texture, self.texture_size, patch.lod, *cb_args)
        else:
            parent_patch = patch.parent
            while parent_patch is not None and parent_patch not in self.map_patch:
                parent_patch = parent_patch.parent
            if parent_patch is not None:
                if callback is not None:
                    callback(*(self.map_patch[parent_patch] + cb_args))
            else:
                if callback is not None:
                    callback(None, None, self.texture_size, patch.lod, *cb_args)

    def load(self, patch, color_space, callback=None, cb_args=()):
        if not patch in self.map_patch:
            self._make_texture(patch, callback, cb_args)
        else:
            callback(*(self.map_patch[patch] + cb_args))

    def texture_ready_cb(self, texture, patch, callback, cb_args):
        #print("READY", patch.str_id())
        self.map_patch[patch] = (texture, self.texture_size, patch.lod)
        if callback is not None:
            callback(*(self.map_patch[patch] + cb_args))

    def _make_texture(self, patch, callback, cb_args):
        if not self.texture_size in ProceduralVirtualTextureSource.tex_generators:
            ProceduralVirtualTextureSource.tex_generators[self.texture_size] = GeneratorPool(settings.patch_pool_size)
            ProceduralVirtualTextureSource.tex_generators[self.texture_size].make_buffer(self.texture_size, self.texture_size, Texture.F_rgba)
        self.tex_generator = ProceduralVirtualTextureSource.tex_generators[self.texture_size]
        if True:#self.shader is None:
            shader = NoiseShader(coord = patch.coord,
                                 noise_source=self.noise,
                                 noise_target=self.target,
                                 offset=(patch.x0, patch.y0, 0.0),
                                 scale=(patch.lod_scale_x, patch.lod_scale_y, 1.0))
            shader.create_and_register_shader(None, None)
        self.texture = Texture()
        self.texture.set_wrap_u(Texture.WMClamp)
        self.texture.set_wrap_v(Texture.WMClamp)
        if patch.lod == 0:
            self.texture.setMinfilter(Texture.FT_linear_mipmap_linear)
        else:
            self.texture.setMinfilter(Texture.FT_linear)
        self.texture.setMagfilter(Texture.FT_linear)

        self.tex_generator.generate(shader, patch.face, self.texture, self.texture_ready_cb, (patch, callback, cb_args))

    def get_texture(self, patch):
        if patch in self.map_patch:
            return self.map_patch[patch]
        else:
            return (None, self.texture_size, patch.lod)
