#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
#
# Cosmonium is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Cosmonium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#

from __future__ import annotations

from math import log2, ceil
import numpy
from panda3d.core import Texture

from ...shaders.base import ShaderProgram
from ...shaders.component import ShaderComponent
from ...shaders.postprocessing.postprocess import PostProcessShader, SimplePostProcessFragmentShader
from ...textures import TextureConfiguration

from ..stage import SceneStage
from ..target import ProcessTarget


class AverageLuminanceFragmentShader(ShaderProgram):

    def __init__(self):
        ShaderProgram.__init__(self, 'fragment')

    def get_shader_id(self) -> str:
        return 'avg-luminance'

    def create_outputs(self, code: list[str]) -> None:
        code.append("out float result;")

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

    def __init__(self, name):
        SceneStage.__init__(self, name)
        self.levels = 0
        self.luminance_textures = []
        self.luminance_tc = None
        self.luminance_shader = None
        self.average_shader = None
        self.downscale_shader = None

    def provides(self):
        return {'average_luminosity': 'color'}

    def requires(self):
        return ['scene']

    def can_render_to_screen(self):
        return False

    def _calc_levels(self, width, height):
        min_size = log2(4)
        x_level = max(log2(width) - min_size, 0)
        y_level = max(log2(height) - min_size, 0)
        return int(ceil(min(x_level, y_level)))

    def _create_luminance_shader(self):
        self.luminance_shader = PostProcessShader(
            fragment_shader=SimplePostProcessFragmentShader(LuminanceFragmentShader(), output_type='float')
        )
        self.luminance_shader.create(None, None)

    def _create_average_shader(self):
        self.average_shader = PostProcessShader(fragment_shader=AverageLuminanceFragmentShader())
        self.average_shader.create(None, None)

    def _create_downscale_shader(self):
        self.downscale_shader = PostProcessShader(fragment_shader=LuminanceDownscaleFragmentShader())
        self.downscale_shader.create(None, None)

    def _create_textures_for_level(self, width, height, level):
        scale = 1 << level
        self.luminance_textures.append(
            self.luminance_tc.create_2d(f"luminance_{level}", max(1, width // scale), max(1, height // scale))
        )

    def _create_downscale_target_for_level(self, pipeline, level, to_ram):
        scale = 1 << level
        target = ProcessTarget(f"luminance_downscale_{level}")
        target.set_relative_size((1.0 / scale, 1.0 / scale))
        target.add_color_target(
            (32, 0, 0, 0), srgb_colors=False, texture=self.luminance_textures[level], to_ram=to_ram
        )
        self.add_target(target)
        target.create(pipeline)
        target.set_shader(self.downscale_shader)
        target.root.set_shader_input('source', self.luminance_textures[level - 1])

    def create(self, pipeline):
        self._create_luminance_shader()
        width = self.win.get_x_size()
        height = self.win.get_y_size()
        if False:
            self._create_average_shader()
            self.luminance_tc = TextureConfiguration(
                format=Texture.F_r32,
                wrap_u=Texture.WM_border_color,
                wrap_v=Texture.WM_border_color,
                minfilter=Texture.FT_linear_mipmap_linear,
                magfilter=Texture.FT_linear,
            )
            self.luminance_textures.append(self.luminance_tc.create_2d("luminance", width, height))
            target = ProcessTarget("luminance")
            target.add_color_target((32, 0, 0, 0), srgb_colors=False, texture=self.luminance_textures[0])
            self.add_target(target)
            target.create(pipeline)
            target.set_shader(self.luminance_shader)
            target.root.set_shader_input('scene', self.get_source('scene'))
            target = ProcessTarget("average_luminosity")
            target.set_fixed_size((1, 1))
            target.add_color_target((32, 0, 0, 0), srgb_colors=False, to_ram=True)
            self.add_target(target)
            target.create(pipeline)
            target.set_shader(self.average_shader)
            target.root.set_shader_input('source', self.luminance_textures[0])
        else:
            self._create_downscale_shader()
            self.levels = self._calc_levels(width, height)
            self.luminance_tc = TextureConfiguration(
                format=Texture.F_r32,
                wrap_u=Texture.WM_border_color,
                wrap_v=Texture.WM_border_color,
                minfilter=Texture.FT_linear,
                magfilter=Texture.FT_linear,
            )
            for level in range(self.levels):
                self._create_textures_for_level(width, height, level)
            target = ProcessTarget("luminance")
            target.add_color_target((32, 0, 0, 0), srgb_colors=False, texture=self.luminance_textures[0])
            self.add_target(target)
            target.create(pipeline)
            target.set_shader(self.luminance_shader)
            target.root.set_shader_input('scene', self.get_source('scene'))
            for level in range(1, self.levels):
                to_ram = level == self.levels - 1
                self._create_downscale_target_for_level(pipeline, level, to_ram)

    def update_win_size(self, size):
        SceneStage.update_win_size(self, size)
        width, height = size
        if True:
            if len(self.luminance_textures) > 0:
                new_levels = self._calc_levels(width, height)
                if new_levels > self.levels:
                    self.remove_target_by_name(f"luminance_downscale_{self.levels - 1}")
                    # Add new levels
                    for level in range(self.levels - 1, new_levels):
                        self._create_textures_for_level(width, height, level)
                    for level in range(self.levels - 1, new_levels):
                        to_ram = level == new_levels - 1
                        self._create_downscale_target_for_level(self.pipeline, level, to_ram)
                    self.pipeline.request_slots_update()
                elif new_levels < self.levels:
                    # Remove levels
                    for level in range(new_levels - 1, self.levels):
                        self.remove_target_by_name(f"luminance_downscale_{level}")
                    self.luminance_textures = self.luminance_textures[:new_levels]
                    self._create_downscale_target_for_level(self.pipeline, new_levels - 1, to_ram=True)
                    self.pipeline.request_slots_update()
                self.levels = new_levels
                for i in range(self.levels):
                    scale = 1 << i
                    self.luminance_textures[i].set_x_size(max(1, width // scale))
                    self.luminance_textures[i].set_y_size(max(1, height // scale))

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
