#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2023 Laurent Deru.
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

from panda3d.core import Texture

from ...textures import TextureConfiguration
from ...shaders.postprocessing.postprocess import PostProcessShader, SimplePostProcessFragmentShader
from ...shaders.base import ShaderProgram

from ..stage import SceneStage
from ..target import ProcessTarget

from .bloom_threshold import LuminanceThresholdFragmentShader


class BlurPassFragmentShader(ShaderProgram):

    def __init__(self, horizontal: bool):
        ShaderProgram.__init__(self, 'fragment')
        self.horizontal = horizontal

    def get_shader_id(self) -> str:
        if self.horizontal:
            return 'blur-hor'
        else:
            return 'blur-vert'

    def create_outputs(self, code: list[str]) -> None:
        code.append('out vec3 result;')

    def create_uniforms(self, code: list[str]) -> None:
        code.append('uniform sampler2D scene;')

    def create_body(self, code: list[str]) -> None:
        code.append('  const float weights[5] = float[5](0.227027, 0.1945946, 0.1216216, 0.054054, 0.016216);')
        code.append('  vec2 texcoord = gl_FragCoord.xy / textureSize(scene, 0);')
        code.append('  vec2 tex_offset = 1.0 / textureSize(scene, 0);')

        code.append('  result = textureLod(scene, texcoord, 0).rgb * weights[0];')
        code.append('  for(int i = 1; i < 5; ++i)')
        code.append('  {')
        if self.horizontal:
            code.append('    result += textureLod(scene, texcoord + vec2(tex_offset.x * i, 0.0), 0).rgb * weights[i];')
            code.append('    result += textureLod(scene, texcoord - vec2(tex_offset.x * i, 0.0), 0).rgb * weights[i];')
        else:
            code.append('    result += textureLod(scene, texcoord + vec2(0.0, tex_offset.y * i), 0).rgb * weights[i];')
            code.append('    result += textureLod(scene, texcoord - vec2(0.0, tex_offset.y * i), 0).rgb * weights[i];')
        code.append('  }')


class BlurBloomStage(SceneStage):

    def __init__(self, name, colors):
        SceneStage.__init__(self, name)
        self.colors = colors

    def provides(self):
        return {'bloom': 'color'}

    def requires(self):
        return ['scene']

    def create(self, pipeline):
        target = ProcessTarget("brightness_threshold")
        target.add_color_target(self.colors, srgb_colors=False,
                                config=TextureConfiguration(wrap_u=Texture.WM_clamp, wrap_v=Texture.WM_clamp))
        self.add_target(target)
        target.create(pipeline)
        shader = PostProcessShader(fragment_shader=SimplePostProcessFragmentShader(LuminanceThresholdFragmentShader()))
        shader.create(None, None)
        target.set_shader(shader)
        target.root.set_shader_input("max_luminance", pipeline.max_luminance)
        target.root.set_shader_input('scene', self.get_source('scene'))

        target = ProcessTarget("bloom_horizontal")
        target.add_color_target(self.colors, srgb_colors=False,
                                config=TextureConfiguration(wrap_u=Texture.WM_clamp, wrap_v=Texture.WM_clamp))
        self.add_target(target)
        target.create(pipeline)
        horizontal_shader = PostProcessShader(fragment_shader=BlurPassFragmentShader(horizontal=True))
        horizontal_shader.create(None, None)
        target.set_shader(horizontal_shader)
        target.root.set_shader_input('scene', self.targets[0].get_attachment('color'))

        target = ProcessTarget("bloom_vertical")
        target.add_color_target(self.colors, srgb_colors=False,
                                config=TextureConfiguration(wrap_u=Texture.WM_clamp, wrap_v=Texture.WM_clamp))
        self.add_target(target)
        target.create(pipeline)
        vertical_shader = PostProcessShader(fragment_shader=BlurPassFragmentShader(horizontal=False))
        vertical_shader.create(None, None)
        target.set_shader(vertical_shader)
        target.root.set_shader_input('scene', self.targets[1].get_attachment('color'))

        buffers = [self.targets[1].get_attachment('color'), self.targets[2].get_attachment('color')]
        even = True

        for i in range(5):
            target = ProcessTarget(f"bloom_horizontal_{i}")
            target.add_color_target(self.colors, srgb_colors=False, texture=buffers[0 if even else 1])
            self.add_target(target)
            target.create(pipeline)
            target.set_shader(horizontal_shader)
            target.root.set_shader_input('scene', buffers[1 if even else 0])

            target = ProcessTarget(f"bloom_vertical_{i}")
            target.add_color_target(self.colors, srgb_colors=False, texture=buffers[1 if even else 0])
            self.add_target(target)
            target.create(pipeline)
            target.set_shader(vertical_shader)
            target.root.set_shader_input('scene', buffers[0 if even else 1])

    def update(self, pipeline):
        self.targets[0].root.set_shader_input("max_luminance", pipeline.max_luminance)
