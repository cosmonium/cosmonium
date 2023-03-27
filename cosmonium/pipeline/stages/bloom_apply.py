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
from ..target import ProcessTarget


class BloomApplyFragmentShader(ShaderComponent):

    def get_id(self):
        return 'bloom-apply'

    def fragment_uniforms(self, code):
        code.append("uniform sampler2D bloom;")

    def fragment_shader(self, code):
        code.append('  vec3 bloom_intensity = textureLod(bloom, texcoord, 0).xyz;')
        code.append('  result = pixel_color + bloom_intensity;')


class BloomApplyStage(SceneStage):

    def __init__(self, name, colors):
        SceneStage.__init__(self, name)
        self.colors = colors

    def provides(self):
        return {'scene': 'color'}

    def requires(self):
        return ['scene', 'bloom']

    def create(self, pipeline):
        target = ProcessTarget("bloom")
        target.add_color_target(self.colors, srgb_colors=False)
        self.add_target(target)
        target.create(pipeline)
        shader = PostProcessShader(fragment_shader=SimplePostProcessFragmentShader(BloomApplyFragmentShader()))
        shader.create(None, None)
        target.set_shader(shader)
        source = self.sources['scene']
        target.root.set_shader_input('scene', source.get_output('scene'))
        source = self.sources['bloom']
        target.root.set_shader_input('bloom', source.get_output('bloom'))
