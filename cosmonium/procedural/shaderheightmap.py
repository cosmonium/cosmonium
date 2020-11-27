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

from .generator import TexGenerator, GeneratorPool
from .shadernoise import NoiseShader, FloatTarget

from ..heightmap import TextureHeightmapBase, HeightmapPatch, HeightmapPatchFactory
from ..textures import TexCoord
from .. import settings

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

    def do_load(self, shape, callback, cb_args):
        if not self.tex_id in ShaderHeightmap.tex_generators:
            ShaderHeightmap.tex_generators[self.tex_id] = TexGenerator()
            if settings.encode_float:
                texture_format = Texture.F_rgba
            else:
                texture_format = Texture.F_r32
            ShaderHeightmap.tex_generators[self.tex_id].make_buffer(self.width, self.height, texture_format)
        tex_generator = ShaderHeightmap.tex_generators[self.tex_id]
        if self.shader is None:
            self.shader = NoiseShader(noise_source=self.noise,
                                      noise_target=FloatTarget(),
                                      coord = self.coord,
                                      offset = self.offset,
                                      scale = self.scale)
            self.shader.create_and_register_shader(None, None)
        tex_generator.generate(self.shader, 0, self.texture, self.heightmap_ready_cb, (callback, cb_args))

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
                 coord=TexCoord.Cylindrical, face=0, border=1):
        HeightmapPatch.__init__(self, parent, x0, y0, x1, y1,
                              width, height,
                              scale,
                              coord, face, border)
        self.shader = None
        self.noise = noise
        self.tex_generator = None

    def apply(self, patch):
        patch.instance.set_shader_input("heightmap_%s" % self.parent.name, self.texture)

    def do_load(self, patch, callback, cb_args):
        if not self.width in ShaderHeightmapPatch.tex_generators:
            ShaderHeightmapPatch.tex_generators[self.width] = GeneratorPool(settings.patch_pool_size)
            if settings.encode_float:
                texture_format = Texture.F_rgba
            else:
                texture_format = Texture.F_r32
            ShaderHeightmapPatch.tex_generators[self.width].make_buffer(self.width, self.height, texture_format)
        tex_generator = ShaderHeightmapPatch.tex_generators[self.width]
        if self.shader is None:
            self.shader = NoiseShader(coord=self.coord,
                                      noise_source=self.noise,
                                      noise_target=FloatTarget(),
                                      offset=(self.x0, self.y0, 0.0),
                                      scale=(self.lod_scale_x, self.lod_scale_y, 1.0))
            self.shader.create_and_register_shader(None, None)
        tex_generator.generate(self.shader, self.face, self.texture, self.heightmap_ready_cb, (callback, cb_args))
