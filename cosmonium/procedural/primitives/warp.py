#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2026 Laurent Deru.
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


from ...parameters import AutoUserParameter, ParametersGroup
from ..shadernoise import NoiseSource


class NoiseWarp(NoiseSource):
    def __init__(self, noise_main, noise_warp, scale=4.0, name=None, ranges={}):
        NoiseSource.__init__(self, name, 'warp', ranges)
        self.noise_main = noise_main
        self.noise_warp = noise_warp
        self.scale = scale

    def get_id(self):
        return self.noise_main.get_id() + "-warp-" + self.noise_warp.get_id()

    def noise_uniforms(self, code):
        self.noise_main.noise_uniforms(code)
        self.noise_warp.noise_uniforms(code)
        code += ["uniform float %s_scale;" % self.str_id]

    def noise_extra(self, program, code):
        self.noise_main.noise_extra(program, code)
        self.noise_warp.noise_extra(program, code)

    def noise_func(self, code):
        self.noise_main.noise_func(code)
        self.noise_warp.noise_func(code)
        code.append('float noise_warp_%d(vec3 point)' % self.num_id)
        code.append('{')
        code.append('  vec3 warped_point;')
        code.append('  float value;')
        self.noise_warp.noise_value(code, 'warped_point.x', 'point')
        self.noise_warp.noise_value(code, 'warped_point.y', 'point + vec3(1, 2, 3)')
        self.noise_warp.noise_value(code, 'warped_point.z', 'point + vec3(4, 3, 2)')
        self.noise_main.noise_value(code, 'value', 'point + %s_scale * warped_point' % self.str_id)
        code.append('  return value;')
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_warp_%d(%s);' % (value, self.num_id, point))

    def update(self, instance):
        self.noise_main.update(instance)
        self.noise_warp.update(instance)
        instance.set_shader_input('%s_scale' % self.str_id, self.scale)

    def get_user_parameters(self):
        group = ParametersGroup(
            self.name,
            AutoUserParameter(
                'scale',
                'scale',
                self,
                AutoUserParameter.TYPE_FLOAT,
                value_range=self.ranges.get('scale'),
            ),
        )
        group.add_parameters(self.noise_main.get_user_parameters())
        group.add_parameters(self.noise_wrap.get_user_parameters())
        return [group]
