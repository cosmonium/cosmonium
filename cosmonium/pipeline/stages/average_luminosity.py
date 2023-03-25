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


from __future__ import annotations

from math import log2, ceil
import numpy

from panda3d.core import Texture

from ...shaders.postprocessing.postprocess import PostProcessShader, SimplePostProcessFragmentShader
from ...shaders.base import ShaderProgram
from ...shaders.component import ShaderComponent
from ...textures import TextureConfiguration

from ..stage import SceneStage
from ..target import ProcessTarget


class AverageLuminanceFragmentShader(ShaderProgram):
    def __init__(self):
        ShaderProgram.__init__(self, 'fragment')

    def get_shader_id(self) -> str:
        return 'avg-luminance'

    def create_outputs(self, code: list[str]) -> None:
        code.append(f"out float result;")

    def create_uniforms(self, code: list[str]) -> None:
        code.append("uniform sampler2D source;")

    def create_body(self, code: list[str]) -> None:
        code.append("  result = textureLod(source, vec2(0.5, 0.5), 1000).r;")


class LuminanceFragmentShader(ShaderComponent):
    def get_id(self) -> str:
        return 'luminance'

    def fragment_shader(self, code: list[str]) -> None:
        code.append('  result = dot(pixel_color, vec3(0.2126, 0.7152, 0.0722));')


class LuminanceDownscaleFragmentShader(ShaderProgram):
    def __init__(self):
        ShaderProgram.__init__(self, 'fragment')

    def get_shader_id(self) -> str:
        return 'luminance-downscale'

    def create_outputs(self, code: list[str]) -> None:
        code.append('out float result;')

    def create_uniforms(self, code: list[str]) -> None:
        code.append('uniform sampler2D source;')

    def create_body(self, code: list[str]) -> None:
        code.append('  vec2 source_texel_size = 1.0 / textureSize(source, 0);')
        code.append('  vec2 source_texcoord = gl_FragCoord.xy * 2 * source_texel_size;')
        code.append('  float tl = textureLod(source, source_texcoord                                     , 0).r;')
        code.append('  float tr = textureLod(source, source_texcoord + source_texel_size * vec2(1.0, 0.0), 0).r;')
        code.append('  float br = textureLod(source, source_texcoord + source_texel_size * vec2(1.0, 1.0), 0).r;')
        code.append('  float bl = textureLod(source, source_texcoord + source_texel_size * vec2(0.0, 1.0), 0).r;')
        code.append('  result = (tl + tr + br + bl) / 4.0;')


class AverageLuminosityStage(SceneStage):
    def provides(self):
        return {'average_luminosity': 'color'}

    def requires(self):
        return ['scene']

    def can_render_to_screen(self):
        return False

    def create(self, pipeline):
        width = self.win.get_x_size()
        height = self.win.get_y_size()
        min_size = log2(4)
        x_level = max(log2(width) - min_size, 0)
        y_level = max(log2(height) - min_size, 0)
        self.levels = int(ceil(min(x_level, y_level)))
        if False:
            self.luminance_textures = []
            width = self.win.get_x_size()
            height = self.win.get_y_size()
            luminance_tc = TextureConfiguration(
                format=Texture.F_r32,
                wrap_u=Texture.WM_border_color, wrap_v=Texture.WM_border_color,
                minfilter=Texture.FT_linear_mipmap_linear,
                magfilter=Texture.FT_linear)
            self.luminance_textures.append(luminance_tc.create_2d("luminance", width, height))
            target = ProcessTarget("luminance")
            target.add_color_target((32, 0, 0, 0), srgb_colors=False, texture=self.luminance_textures[0])
            self.add_target(target)
            target.create(pipeline)
            shader = PostProcessShader(fragment_shader=SimplePostProcessFragmentShader(LuminanceFragmentShader(), output_type='float'))
            shader.create(None, None)
            target.set_shader(shader)
            target.root.set_shader_input('scene', self.get_source('scene'))
            target = ProcessTarget("average_luminosity")
            target.set_fixed_size((1, 1))
            target.add_color_target((32, 0, 0, 0), srgb_colors=False, to_ram=True)
            self.add_target(target)
            target.create(pipeline)
            shader = PostProcessShader(fragment_shader=AverageLuminanceFragmentShader())
            shader.create(None, None)
            target.set_shader(shader)
            target.root.set_shader_input('source', self.luminance_textures[0])
        else:
            self.luminance_textures = []
            luminance_tc = TextureConfiguration(
                format=Texture.F_r32,
                wrap_u=Texture.WM_border_color, wrap_v=Texture.WM_border_color,
                minfilter=Texture.FT_linear,
                magfilter=Texture.FT_linear)
            for i in range(self.levels):
                scale = 1 << i
                self.luminance_textures.append(luminance_tc.create_2d(f"luminance_{i}", max(1, width // scale), max(1, height // scale)))
            target = ProcessTarget("luminance")
            target.add_color_target((32, 0, 0, 0), srgb_colors=False, texture=self.luminance_textures[0])
            self.add_target(target)
            target.create(pipeline)
            shader = PostProcessShader(fragment_shader=SimplePostProcessFragmentShader(LuminanceFragmentShader(), output_type='float'))
            shader.create(None, None)
            target.set_shader(shader)
            target.root.set_shader_input('scene', self.get_source('scene'))

            shader = PostProcessShader(fragment_shader=LuminanceDownscaleFragmentShader())
            shader.create(None, None)
            for level in range(1, self.levels):
                scale = 1 << level
                target = ProcessTarget(f"luminance_downscale_{level}")
                target.set_relative_size((1.0 / scale, 1.0 / scale))
                target.add_color_target((32, 0, 0, 0), srgb_colors=False, texture=self.luminance_textures[level], to_ram=(level == self.levels - 1))
                self.add_target(target)
                target.create(pipeline)
                target.set_shader(shader)
                target.root.set_shader_input('source', self.luminance_textures[level - 1])

    def extract_level(self):
        texture = self.targets[-1].get_attachment('color')
        data = texture.get_ram_image()
        if len(data) > 0:
            np_buffer = numpy.frombuffer(data, numpy.float32)
            np_buffer.shape = (texture.get_x_size(), texture.get_y_size(), 1)
            value = np_buffer.mean()
            return value
        else:
            return 0.0001
