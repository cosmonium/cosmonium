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


from ...parameters import ParametersGroup, AutoUserParameter
from ..shadernoise import BasicNoiseSource, NoiseSource


class PositionMap(BasicNoiseSource):
    def __init__(self, noise, offset=0.0, scale=1.0, dynamic=True, name=None):
        BasicNoiseSource.__init__(self, noise, name, 'pos')
        self.offset = offset
        self.scale = scale
        self.dynamic = dynamic

    def get_id(self):
        if self.dynamic:
            return ('pos-%d-' % self.num_id) + self.noise.get_id()
        else:
            return ('pos-%g-%g-' % (self.offset, self.scale)) + self.noise.get_id()

    def noise_uniforms(self, code):
        BasicNoiseSource.noise_uniforms(self, code)
        if self.dynamic:
            code.append("uniform vec2 %s_params;" % self.str_id)

    def noise_value(self, code, value, point):
        if self.dynamic:
            self.noise.noise_value(
                code,
                value,
                '(%s * %s_params.x + %s_params.y)' % (point, self.str_id, self.str_id),
            )
        else:
            self.noise.noise_value(code, value, '(%s * %g + %g)' % (point, self.scale, self.offset))

    def update(self, instance):
        BasicNoiseSource.update(self, instance)
        if self.dynamic:
            instance.set_shader_input('%s_params' % self.str_id, (self.scale, self.offset))

    def get_user_parameters(self):
        parameters = BasicNoiseSource.get_user_parameters(self)
        if isinstance(parameters, ParametersGroup):
            group = parameters
        else:
            group = ParametersGroup(self.noise.name)
            group.add_parameters(parameters)
        group.add_parameters(
            AutoUserParameter('Scale', 'scale', self, param_type=AutoUserParameter.TYPE_FLOAT),
            AutoUserParameter('Offset', 'offset', self, param_type=AutoUserParameter.TYPE_FLOAT),
        )
        return [group]


class Noise1D(BasicNoiseSource):
    def __init__(self, noise, axis, name=None):
        BasicNoiseSource.__init__(self, noise, name, 'axis')
        self.axis = axis

    def get_id(self):
        return ('axis-%s-' % (self.axis)) + self.noise.get_id()

    def noise_func(self, code):
        BasicNoiseSource.noise_func(self, code)
        code.append('float noise_axis_%d(vec3 point)' % self.num_id)
        code.append('{')
        code.append('  float value;')
        code.append('  vec3 point_1d = vec3(0);')
        code.append('  point_1d.%s = point.%s;' % (self.axis, self.axis))
        self.noise.noise_value(code, 'value', 'point_1d')
        code.append('  return value;')
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_axis_%d(%s);' % (value, self.num_id, point))


class NoiseRotate(NoiseSource):
    def __init__(self, noise_main, noise_angle, axis, name=None):
        NoiseSource.__init__(self, name, 'rot' + axis)
        self.noise_main = noise_main
        self.noise_angle = noise_angle
        self.axis = axis

    def get_id(self):
        return self.noise_main.get_id() + "-rot" + self.axis + "-" + self.noise_angle.get_id()

    def noise_uniforms(self, code):
        self.noise_main.noise_uniforms(code)
        self.noise_angle.noise_uniforms(code)

    def noise_extra(self, program, code):
        self.noise_main.noise_extra(program, code)
        self.noise_angle.noise_extra(program, code)

    def noise_func(self, code):
        self.noise_main.noise_func(code)
        self.noise_angle.noise_func(code)
        code.append('float noise_rot%s_%d(vec3 point)' % (self.axis, self.num_id))
        code.append('{')
        code.append('  float value;')
        code.append('  float theta;')
        self.noise_angle.noise_value(code, 'theta', 'point')
        code.append('  float cos_theta = cos(theta);')
        code.append('  float sin_theta = sin(theta);')
        if self.axis == 'x':
            code.append('  mat3 rot = mat3(1.0, 0.0,       0.0,')
            code.append('                  0.0, cos_theta, -sin_theta,')
            code.append('                  0.0, sin_theta, cos_theta);')
        elif self.axis == 'y':
            code.append('  mat3 rot = mat3(cos_theta,  0.0, sin_theta,')
            code.append('                  0.0,        1.0, 0.0,')
            code.append('                  -sin_theta, 0.0, cos_theta);')
        else:
            code.append('  mat3 rot = mat3(cos_theta, -sin_theta, 0.0,')
            code.append('                  sin_theta, cos_theta,  0.0,')
            code.append('                  0.0,       0.0,        1.0);')
        self.noise_main.noise_value(code, 'value', 'rot * point')
        code.append('  return value;')
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_rot%s_%d(%s);' % (value, self.axis, self.num_id, point))

    def update(self, instance):
        self.noise_main.update(instance)
        self.noise_angle.update(instance)

    def get_user_parameters(self):
        group = ParametersGroup(self.name)
        group.add_parameters(self.noise_main.get_user_parameters())
        group.add_parameters(self.noise_angle.get_user_parameters())
        return [group]
