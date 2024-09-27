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

from ...shaders.component import ShaderComponent
from ...shaders.postprocessing.postprocess import PostProcessShader, SimplePostProcessFragmentShader

from ..stage import SceneStage
from ..target import ScreenTarget, ProcessTarget


class PassthroughFragmentShader(ShaderComponent):

    def get_id(self):
        return 'passthrough'

    def fragment_shader(self, code):
        code.append('    result = pixel_color;')


class PassthroughStage(SceneStage):

    def __init__(self, name, colors):
        SceneStage.__init__(self, name)
        self.colors = colors

    def provides(self):
        return {'scene': 'color'}

    def requires(self):
        return ['scene']

    def create(self, pipeline):
        if self.screen_stage:
            target = ScreenTarget("passthrough")
        else:
            target = ProcessTarget("passthrough")
            target.add_color_target(self.colors)
        self.add_target(target)
        target.create(pipeline)
        shader = PostProcessShader(fragment_shader=SimplePostProcessFragmentShader(PassthroughFragmentShader()))
        shader.create(None, None)
        target.set_shader(shader)
        target.root.set_shader_input('scene', self.get_source('scene'))
