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

from ...shaders.postprocessing.postprocess import PostProcessShader, SimplePostProcessFragmentShader
from ...shaders.component import ShaderComponent

from ..stage import SceneStage
from ..target import ScreenTarget, ProcessTarget


class ColorCorrectionFragmentShader(ShaderComponent):

    def get_id(self):
        return 'color-correction-srgb'

    def fragment_extra(self, code):
        code.append('#pragma include "shaders/includes/colorspaces.glsl"')

    def fragment_shader(self, code):
        code.append('  result = vec4(linear_to_srgb(pixel_color), 1);')


class ColorCorrectionStage(SceneStage):

    def __init__(self, name, colors):
        SceneStage.__init__(self, name)
        self.colors = colors

    def provides(self):
        return {'scene': 'color'}

    def requires(self):
        return ['scene']

    def create(self, pipeline):
        if self.screen_stage:
            target = ScreenTarget("srgb")
        else:
            target = ProcessTarget("srgb")
            target.add_color_target(self.colors)
        self.add_target(target)
        target.create(pipeline)
        shader = PostProcessShader(fragment_shader=SimplePostProcessFragmentShader(ColorCorrectionFragmentShader()))
        shader.create(None, None)
        target.set_shader(shader)
        target.root.set_shader_input('scene', self.get_source('scene'))
