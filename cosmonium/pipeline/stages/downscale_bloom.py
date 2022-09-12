#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2022 Laurent Deru.
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

from panda3d.core import Texture

from ...shaders.postprocessing.postprocess import PostProcessShader, SimplePostProcessFragmentShader
from ...shaders.base import ShaderProgram
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
        self.levels = 10
        self.bloom_textures: list[Texture] = []
        self.target_textures: list[Texture] = []

    def provides(self):
        return {'bloom': 'color'}

    def requires(self):
        return ['scene']

    def create(self, pipeline):
        width = self.win.get_x_size()
        height = self.win.get_y_size()
        bloom_tc = TextureConfiguration(
            format=Texture.F_rgb32,
            wrap_u=Texture.WM_clamp, wrap_v=Texture.WM_clamp,
            minfilter=Texture.FT_linear,
            magfilter=Texture.FT_linear)
        for i in range(self.levels):
            scale = 1 << i
            self.bloom_textures.append(bloom_tc.create_2d(f"bloom_{i}", width // scale, height // scale))
            self.target_textures.append(bloom_tc.create_2d(f"bloom_target_{i}", width // scale, height // scale))

        target = ProcessTarget("brightness_threshold")
        target.add_color_target(self.colors, srgb_colors=False, texture=self.bloom_textures[0])
        self.add_target(target)
        target.create(pipeline)
        shader = PostProcessShader(fragment_shader=SimplePostProcessFragmentShader(LuminanceThresholdFragmentShader()))
        shader.create(None, None)
        target.set_shader(shader)
        target.root.set_shader_input("max_luminance", pipeline.max_luminance)
        target.root.set_shader_input('scene', self.get_source('scene'))

        shader = PostProcessShader(fragment_shader=BloomDownscaleFragmentShader())
        shader.create(None, None)
        for level in range(1, self.levels):
            scale = 1 << level
            target = ProcessTarget(f"bloom_downscale_{level}")
            target.set_relative_size((1.0 / scale, 1.0 / scale))
            target.add_color_target(self.colors, srgb_colors=False, texture=self.bloom_textures[level])
            self.add_target(target)
            target.create(pipeline)
            target.set_shader(shader)
            target.root.set_shader_input('source', self.bloom_textures[level - 1])

        shader = PostProcessShader(fragment_shader=BloomUpscaleFragmentShader())
        shader.create(None, None)
        for level in range(self.levels - 1, 0, -1):
            scale = 1 << (level - 1)
            target = ProcessTarget(f"bloom_upscale_{level}")
            target.set_relative_size((1.0 / scale, 1.0 / scale))
            target.add_color_target(self.colors, srgb_colors=False, texture=self.target_textures[level - 1])
            self.add_target(target)
            target.create(pipeline)
            target.set_shader(shader)
            target.root.set_shader_input('source', self.bloom_textures[level - 1])
            target.root.set_shader_input('upper', self.target_textures[level])

    def update(self, pipeline):
        self.targets[0].root.set_shader_input("max_luminance", pipeline.max_luminance)
        #for i in range(self.levels):
        #    self.target_textures[i].clear_image()

    def update_win_size(self, size):
        SceneStage.update_win_size(self, size)
        if len(self.bloom_textures) > 0:
            width, height = size
            for i in range(self.levels):
                scale = 1 << i
                self.bloom_textures[i].set_x_size(width // scale)
                self.bloom_textures[i].set_y_size(height // scale)
                self.target_textures[i].set_x_size(width // scale)
                self.target_textures[i].set_y_size(height // scale)
