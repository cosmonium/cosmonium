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
from .shadernoise import NoiseShader, FloatTarget

from ..heightmap import TextureHeightmapBase, HeightmapPatch, HeightmapPatchFactory
from ..textures import TexCoord
from .. import settings

class HeightmapGenerationStage(RenderStage):
    def __init__(self, coord, width, height, noise_source):
        RenderStage.__init__(self, "heightmap", (width, height))
        self.coord = coord
        self.noise_source = noise_source

    def create_shader(self):
        shader = NoiseShader(coord=self.coord, noise_source=self.noise_source, noise_target=FloatTarget())
        shader.create_and_register_shader(None, None)
        return shader

    def create(self):
        self.target = RenderTarget()
        (width, height) = self.get_size()
        self.target.make_buffer(width, height, Texture.F_r32, to_ram=True)
        self.target.set_shader(self.create_shader())

    def create_textures(self, shader_data):
        texture = Texture()
        texture.set_wrap_u(Texture.WM_clamp)
        texture.set_wrap_v(Texture.WM_clamp)
        texture.set_anisotropic_degree(0)
        texture.set_minfilter(Texture.FT_linear)
        texture.set_magfilter(Texture.FT_linear)
        return texture

class ShaderHeightmap(TextureHeightmapBase):
    tex_generators = {}

    def __init__(self, name, width, height, height_scale, noise, offset=None, scale=None, coord = TexCoord.Cylindrical, interpolator=None):
        TextureHeightmapBase.__init__(self, name, width, height, height_scale, 1.0, 1.0, interpolator)
        self.noise = noise
        self.offset = offset
        self.scale = scale
        self.coord = coord
        self.shader = None

    def set_noise(self, noise):
        self.noise = noise
        self.shader = None
        self.reset()

    def set_offset(self, offset):
        self.offset = offset
        if self.shader is not None:
            self.shader.offset = offset
        self.reset()

    def set_scale(self, scale):
        self.scale = scale
        if self.shader is not None:
            self.shader.scale = scale
        self.reset()

    def apply(self, shape):
        shape.instance.set_shader_input("heightmap_%s" % self.name, self.texture)

    async def load(self, patch):
        result = await self.do_load(patch)
        data = result['heightmap']
        self.configure_heightmap(data)

    def do_load(self, shape):
        if not self.tex_id in ShaderHeightmap.tex_generators:
            chain = GeneratorChain()
            stage = HeightmapGenerationStage(self.coord, self.width, self.height, self.noise)
            chain.add_stage(stage)
            chain.create()
            ShaderHeightmapPatch.tex_generators[self.tex_id] = chain
        tex_generator = ShaderHeightmap.tex_generators[self.tex_id]
        if self.shader is None:
            self.shader = NoiseShader(noise_source=self.noise,
                                      noise_target=FloatTarget(),
                                      coord = self.coord,
                                      offset = self.offset,
                                      scale = self.scale)
            self.shader.create_and_register_shader(None, None)
        return tex_generator.generate(self.shader, 0, self.texture)

class ShaderHeightmapPatchFactory(HeightmapPatchFactory):
    def __init__(self, noise):
        HeightmapPatchFactory.__init__(self)
        self.noise = noise

    def create_patch(self, *args, **kwargs):
        return ShaderHeightmapPatch.create_from_patch(self.noise, *args, **kwargs)

class ShaderHeightmapPatch(HeightmapPatch):
    tex_generators = {}
    cachable = False
    def __init__(self, noise, parent,
                 x0, y0, x1, y1,
                 width, height,
                 scale=1.0,
                 coord=TexCoord.Cylindrical, face=0, overlap=0):
        HeightmapPatch.__init__(self, parent, x0, y0, x1, y1,
                              width, height,
                              scale,
                              coord, face, overlap)
        self.shader = None
        self.noise = noise
        self.tex_generator = None

    def apply(self, patch):
        if self.texture is None:
            # The heightmap is not available yet, use the parent heightmap instead
            self.calc_sub_patch()
        patch.instance.set_shader_input("heightmap_%s" % self.parent.name, self.texture)

    async def load(self, patch):
        result = await self.do_load(patch)
        data = result['heightmap']
        self.configure_heightmap(data)

    def do_load(self, patch):
        if not self.width in ShaderHeightmapPatch.tex_generators:
            pool = GeneratorPool([])
            for i in range(settings.patch_pool_size):
                chain = GeneratorChain()
                stage = HeightmapGenerationStage(self.coord, self.width, self.height, self.noise)
                chain.add_stage(stage)
                pool.add_chain(chain)
            ShaderHeightmapPatch.tex_generators[self.width] = pool
            pool.create()
        tex_generator = ShaderHeightmapPatch.tex_generators[self.width]
        shader_data = {'heightmap': {'offset': (self.r_x0, self.r_y0, 0.0),
                                     'scale': (self.r_x1 - self.r_x0, self.r_y1 - self.r_y0, 1.0),
                                     'face': self.face
                                    }}
        return tex_generator.generate(shader_data)
