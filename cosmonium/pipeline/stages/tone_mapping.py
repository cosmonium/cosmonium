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


from ...shaders.postprocessing.postprocess import PostProcessShader, SimplePostProcessFragmentShader
from ...shaders.component import ShaderComponent

from ..stage import SceneStage
from ..target import ScreenTarget, ProcessTarget


class SimpleToneMappingFragmentShader(ShaderComponent):
    def __init__(self, tonemapping_func: str, luminance_tonemap: bool):
        self.tonemapping_func = tonemapping_func
        self.luminance_tonemap = luminance_tonemap

    def get_id(self):
        name = 'tonemapping-' + self.tonemapping_func
        if self.luminance_tonemap:
            name += '-luminance'
        return name

    def fragment_extra(self, code):
        code.append('#pragma include "shaders/includes/tonemapping.glsl"')
        if self.luminance_tonemap:
            code.append('#pragma include "shaders/includes/colorspaces.glsl"')

    def fragment_uniforms(self, code):
        code.append("uniform float exposure;")

    def fragment_shader(self, code):
        code.append('  vec3 exposed_color = pixel_color * exposure;')
        if self.luminance_tonemap:
            code.append('  vec3 xyy = linear_to_xyy(pixel_color);')
            code.append('  float exposed_luminance = xyy.z * exposure;')
            code.append(f'  float ldr = {self.tonemapping_func}(exposed_luminance);')
            code.append('  result = xyy_to_linear(vec3(xyy.x, xyy.y, ldr));')
        else:
            code.append(f'  result = vec3({self.tonemapping_func}(exposed_color.r), {self.tonemapping_func}(exposed_color.g), {self.tonemapping_func}(exposed_color.b));')


class ToneMappingStage(SceneStage):
    def __init__(self, name, colors):
        SceneStage.__init__(self, name)
        self.colors = colors

    def provides(self):
        return {'scene': 'color'}

    def requires(self):
        return ['scene']

    def create(self, pipeline):
        if self.screen_stage:
            target = ScreenTarget("tone_mapping")
        else:
            target = ProcessTarget("tone_mapping")
            target.add_color_target(self.colors)
        self.add_target(target)
        target.create(pipeline)
        shader = PostProcessShader(fragment_shader=SimplePostProcessFragmentShader(SimpleToneMappingFragmentShader('tonemap_aces', False)))
        shader.create(None, None)
        target.set_shader(shader)
        target.root.set_shader_input("exposure", 1.0)
        target.root.set_shader_input('scene', self.get_source('scene'))

    def update(self, pipeline):
        self.targets[0].root.set_shader_input("exposure", pipeline.exposure)
