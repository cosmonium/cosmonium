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
        self.target.make_buffer(width, height, Texture.F_rgba, to_ram=False)
        self.target.set_shader(self.create_shader())

    def create_textures(self, shader_data):
        texture = Texture()
        texture.set_wrap_u(Texture.WM_clamp)
        texture.set_wrap_v(Texture.WM_clamp)
        texture.set_anisotropic_degree(0)
        if shader_data['lod'] == 0:
            texture.set_minfilter(Texture.FT_linear_mipmap_linear)
        else:
            texture.set_minfilter(Texture.FT_linear)
        texture.set_magfilter(Texture.FT_linear)
        return {'texture': texture}

    def configure_data(self, data, shape, patch):
        if patch is not None:
            data[self.name] = {'offset': (patch.x0, patch.y0, 0.0),
                               'scale': (patch.x1 - patch.x0, patch.y1 - patch.y0, 1.0),
                               'face': patch.face,
                               'lod': patch.lod
                              }
        else:
            data[self.name] = {'offset': (0.0, 0.0, 0.0),
                               'scale': (1.0, 1.0, 1.0),
                               'face': -1,
                               'lod': 0
                              }

class NoiseTextureGenerator():
    def __init__(self, size, noise, target):
        self.texture_size = size
        self.noise = noise
        self.target = target
        self.tex_generator = None

    def create(self, coord):
        self.tex_generator =  GeneratorChain()
        self.texture_stage = TextureGenerationStage(coord, self.texture_size, self.texture_size, self.noise, self.target)
        self.tex_generator.add_stage(self.texture_stage)
        self.tex_generator.create()

    def clear_all(self):
        if self.tex_generator is not None:
            self.tex_generator.remove()
            self.tex_generator = None

    async def generate(self, shape, patch):
        if self.tex_generator is None:
            self.create(shape.coord)
        shader_data = {}
        self.texture_stage.configure_data(shader_data, shape, patch)
        #print("GEN", patch.str_id())
        result = await self.tex_generator.generate(shader_data)
        texture = result[self.texture_stage.name].get('texture')
        return texture

class ProceduralVirtualTextureSource(TextureSource):
    cached = True
    procedural = True
    def __init__(self, tex_generator, size):
        TextureSource.__init__(self)
        self.texture_size = size
        self.tex_generator = tex_generator

    async def load(self, shape, color_space):
        if self.texture is None:
            self.texture = await self.tex_generator.generate(shape, None)
        return (self.texture, self.texture_size, 0)

    def get_texture(self, shape, strict=False):
        return (self.texture, self.texture_size, 0)

    def clear_all(self):
        self.texture = None
        self.tex_generator.clear_all()

class PatchedProceduralVirtualTextureSource(TextureSource):
    cached = False
    procedural = True
    def __init__(self, tex_generator, size):
        TextureSource.__init__(self)
        self.texture_size = size
        self.map_patch = {}
        self.tex_generator = tex_generator

    def is_patched(self):
        return True

    def child_texture_name(self, patch):
        return None

    def texture_name(self, patch):
        return None

    def can_split(self, patch):
        return True

    async def load(self, patch, color_space):
        #print("LOAD", patch.str_id())
        texture_info = None
        if not patch.str_id() in self.map_patch:
            texture = await self.tex_generator.generate(patch, patch)
            #print("READY", patch.str_id())
            texture_info = (texture, self.texture_size, patch.lod)
            self.map_patch[patch.str_id()] = texture_info
        else:
            texture_info = self.map_patch[patch.str_id()]
        return texture_info

    def clear_patch(self, patch):
        try:
            del self.map_patch[patch.str_id()]
        except KeyError:
            pass

    def clear_all(self):
        self.map_patch = {}
        self.tex_generator.clear_all()

    def get_texture(self, patch, strict=False):
        if patch.str_id() in self.map_patch:
            return self.map_patch[patch.str_id()]
        elif not strict:
            parent_patch = patch.parent
            while parent_patch is not None and parent_patch.str_id() not in self.map_patch:
                parent_patch = parent_patch.parent
            if parent_patch is not None:
                #print(globalClock.getFrameCount(), "USE PARENT", patch.str_id(), parent_patch.str_id())
                return self.map_patch[parent_patch.str_id()]
            else:
                #print(globalClock.getFrameCount(), "NONE")
                return (None, self.texture_size, patch.lod)
        else:
            return (None, self.texture_size, patch.lod)
