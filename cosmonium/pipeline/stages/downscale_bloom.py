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

from math import ceil, log2
from panda3d.core import Texture

from ...shaders.postprocessing.postprocess import PostProcessShader, SimplePostProcessFragmentShader
from ...shaders.base import ShaderProgram, ShaderBase
from ...textures import TextureConfiguration

from ..stage import SceneStage
from ..target import ProcessTarget

from .bloom_threshold import LuminanceThresholdFragmentShader


class BloomDownscaleFragmentShader(ShaderProgram):
    def __init__(self):
        ShaderProgram.__init__(self, 'fragment')

    def get_shader_id(self) -> str:
        return 'bloom-downscale'

    def create_outputs(self, code: list[str]) -> None:
        code.append('out vec4 result;')

    def create_uniforms(self, code: list[str]) -> None:
        code.append('uniform sampler2D source;')

    def create_extra(self, code: list[str]) -> None:
        code.append('#pragma include "shaders/includes/box_filtering.glsl"')

    def create_body(self, code: list[str]) -> None:
        code.append('  vec2 source_texel_size = 1.0 / textureSize(source, 0);')
        code.append('  vec2 source_texcoord = gl_FragCoord.xy * source_texel_size * 2;')
        code.append('  result = filtering_box13(source, source_texcoord, source_texel_size, 0);')


class BloomUpscaleFragmentShader(ShaderProgram):
    def __init__(self):
        ShaderProgram.__init__(self, 'fragment')

    def get_shader_id(self) -> str:
        return 'bloom-upscale'

    def create_outputs(self, code: list[str]) -> None:
        code.append('out vec4 result;')

    def create_uniforms(self, code: list[str]) -> None:
        code.append('uniform sampler2D upper;')
        code.append('uniform sampler2D source;')

    def create_extra(self, code: list[str]) -> None:
        code.append('#pragma include "shaders/includes/box_filtering.glsl"')

    def create_body(self, code: list[str]) -> None:
        code.append('  vec2 upper_texel_size = 1.0 / textureSize(upper, 0);')
        code.append('  vec2 upper_texcoord = (gl_FragCoord.xy) * upper_texel_size * 0.5;')
        code.append('  vec4 filtered = filtering_box9(upper, upper_texcoord, upper_texel_size, 0);')
        code.append('  vec2 source_texel_size = 1.0 / textureSize(source, 0);')
        code.append('  vec2 source_texcoord = gl_FragCoord.xy * source_texel_size;')
        code.append('  result = (textureLod(source, source_texcoord, 0) + filtered) * 0.5;')


class DownscaleBloomStage(SceneStage):
    def __init__(self, name, colors):
        SceneStage.__init__(self, name)
        self.colors = colors
        self.levels: int = 0
        self.brightness_threshold: bool = False
        self.bloom_textures: list[Texture] = []
        self.target_textures: list[Texture] = []
        self.brightness_threshold_shader: ShaderBase = None
        self.downscale_shader: ShaderBase = None
        self.upscale_shader: ShaderBase = None

    def provides(self):
        return {'bloom': 'color'}

    def requires(self):
        return ['scene']

    def create_shaders(self):
        self.brightness_threshold_shader = PostProcessShader(fragment_shader=SimplePostProcessFragmentShader(LuminanceThresholdFragmentShader()))
        self.brightness_threshold_shader.create(None, None)
        self.downscale_shader = PostProcessShader(fragment_shader=BloomDownscaleFragmentShader())
        self.downscale_shader.create(None, None)
        self.upscale_shader = PostProcessShader(fragment_shader=BloomUpscaleFragmentShader())
        self.upscale_shader.create(None, None)

    def _create_textures_for_level(self, width, height, level):
        scale = 1 << level
        self.bloom_textures.append(
            self.bloom_tc.create_2d(f"bloom_{level}", width // scale, height // scale))
        self.target_textures.append(
            self.bloom_tc.create_2d(f"bloom_target_{level}", width // scale, height // scale))


    def _create_downscale_target_for_level(self, pipeline, level):
        scale = 1 << level
        target = ProcessTarget(f"bloom_downscale_{level}")
        target.set_relative_size((1.0 / scale, 1.0 / scale))
        target.add_color_target(self.colors, srgb_colors=False, texture=self.bloom_textures[level])
        self.add_target(target)
        target.create(pipeline)
        target.set_shader(self.downscale_shader)
        target.root.set_shader_input('source', self.bloom_textures[level - 1])


    def _create_upscale_target_for_level(self, pipeline, level):
        scale = 1 << (level - 1)
        target = ProcessTarget(f"bloom_upscale_{level}")
        target.set_relative_size((1.0 / scale, 1.0 / scale))
        target.add_color_target(self.colors, srgb_colors=False, texture=self.target_textures[level - 1])
        self.add_target(target)
        target.create(pipeline)
        target.set_shader(self.upscale_shader)
        target.root.set_shader_input('source', self.bloom_textures[level - 1])
        target.root.set_shader_input('upper', self.target_textures[level])

    def create(self, pipeline):
        self.create_shaders()
        width = self.win.get_x_size()
        height = self.win.get_y_size()
        self.levels = int(ceil(min(log2(width), log2(height))))
        self.bloom_tc = TextureConfiguration(
            format=Texture.F_rgb32,
            wrap_u=Texture.WM_clamp, wrap_v=Texture.WM_clamp,
            minfilter=Texture.FT_linear,
            magfilter=Texture.FT_linear)

        for level in range(self.levels):
            self._create_textures_for_level(width, height, level)

        if self.brightness_threshold:
            target = ProcessTarget("brightness_threshold")
            target.add_color_target(self.colors, srgb_colors=False, texture=self.bloom_textures[0])
            self.add_target(target)
            target.create(pipeline)
            target.set_shader(self.brightness_threshold_shader)
            target.root.set_shader_input("max_luminance", pipeline.max_luminance)
            target.root.set_shader_input('scene', self.get_source('scene'))
        else:
            self.bloom_textures[0] = self.get_source('scene')

        for level in range(1, self.levels):
            self._create_downscale_target_for_level(pipeline, level)

        for level in range(self.levels - 1, 0, -1):
            self._create_upscale_target_for_level(pipeline, level)

    def update(self, pipeline):
        if self.brightness_threshold:
            self.targets[0].root.set_shader_input("max_luminance", pipeline.max_luminance)
        #for i in range(self.levels):
        #    self.target_textures[i].clear_image()

    def update_win_size(self, size):
        SceneStage.update_win_size(self, size)
        width, height = size
        if len(self.bloom_textures) > 0:
            new_levels = int(ceil(min(log2(width), log2(height))))
            if new_levels > self.levels:
                # Add new levels
                for level in range(self.levels, new_levels):
                    self._create_textures_for_level(width, height, level)
                for level in range(self.levels, new_levels):
                    self._create_downscale_target_for_level(self.pipeline, level)
                for level in range(self.levels, new_levels):
                    self._create_upscale_target_for_level(self.pipeline, level)
                self.pipeline.request_slots_update()
            elif new_levels < self.levels:
                # Remove levels
                for level in range(new_levels, self.levels):
                    self.remove_target_by_name(f"bloom_downscale_{level}")
                    self.remove_target_by_name(f"bloom_upscale_{level}")
                self.target_textures = self.target_textures[:new_levels]
            self.levels = new_levels
            for i in range(self.levels):
                scale = 1 << i
                self.bloom_textures[i].set_x_size(width // scale)
                self.bloom_textures[i].set_y_size(height // scale)
                self.target_textures[i].set_x_size(width // scale)
                self.target_textures[i].set_y_size(height // scale)
