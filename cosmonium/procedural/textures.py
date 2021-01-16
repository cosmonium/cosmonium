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

from .generator import RenderTarget, RenderStage, GeneratorChain, GeneratorPool
from ..textures import TextureSource
from .shadernoise import NoiseShader
from .. import settings

class TextureGenerationStage(RenderStage):
    def __init__(self, coord, width, height, noise_source, noise_target):
        RenderStage.__init__(self, "texture", (width, height))
        self.coord = coord
        self.noise_source = noise_source
        self.noise_target = noise_target

    def create_shader(self):
        shader = NoiseShader(coord=self.coord, noise_source=self.noise_source, noise_target=self.noise_target)
        shader.create_and_register_shader(None, None)
        return shader

    def create(self):
        self.target = RenderTarget()
        (width, height) = self.get_size()
        #TODO: Is to_ram is set to False, patch at lod 0 have no texture !
        self.target.make_buffer(width, height, Texture.F_rgba, to_ram=True)
        self.target.set_shader(self.create_shader())

class ProceduralVirtualTextureSource(TextureSource):
    cached = False
    procedural = True
    def __init__(self, noise, target, size):
        TextureSource.__init__(self)
        self.noise = noise
        self.target = target
        self.texture_size = size
        self.map_patch = {}
        self.tex_generator = None

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

    def texture_ready_cb(self, chain, patch, callback, cb_args):
        #print("READY", patch.str_id())
        texture = chain.stages[0].target.texture
        if patch.lod == 0:
            texture.set_minfilter(Texture.FT_linear_mipmap_linear)
        else:
            texture.set_minfilter(Texture.FT_linear)
        self.map_patch[patch] = (texture, self.texture_size, patch.lod)
        if callback is not None:
            callback(*(self.map_patch[patch] + cb_args))

    def create_generator(self, coord):
        self.tex_generator = GeneratorPool([])
        for i in range(settings.patch_pool_size):
            chain = GeneratorChain()
            stage = TextureGenerationStage(coord, self.texture_size, self.texture_size, self.noise, self.target)
            chain.add_stage(stage)
            self.tex_generator.add_chain(chain)
        self.tex_generator.create()

    def _make_texture(self, patch, callback, cb_args):
        if self.tex_generator is None:
            self.create_generator(patch.coord)
        shader_data = {'texture': {'offset': (patch.x0, patch.y0, 0.0),
                                   'scale': (patch.lod_scale_x, patch.lod_scale_y, 1.0),
                                   'face': patch.face
                                  }}

        self.tex_generator.generate(shader_data, self.texture_ready_cb, (patch, callback, cb_args))

    def get_texture(self, patch):
        if patch in self.map_patch:
            return self.map_patch[patch]
        else:
            return (None, self.texture_size, patch.lod)
