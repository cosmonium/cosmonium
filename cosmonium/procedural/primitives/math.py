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
from ..shadernoise import BasicNoiseSource, NoiseSource


class AbsNoise(BasicNoiseSource):
    def __init__(self, noise, name=None):
        BasicNoiseSource.__init__(self, noise, name, 'abs')

    def get_id(self):
        return 'abs-' + self.noise.get_id()

    def noise_value(self, code, value, point):
        tmp = self.create_tmp(code)
        self.noise.noise_value(code, tmp, point)
        code.append('          %s = abs(%s);' % (value, tmp))


class NoiseExp(BasicNoiseSource):
    def __init__(self, noise, name=None):
        BasicNoiseSource.__init__(self, noise, name, 'exp')

    def get_id(self):
        return 'exp-' + self.noise.get_id()

    def noise_value(self, code, value, point):
        tmp = self.create_tmp(code)
        self.noise.noise_value(code, tmp, point)
        code.append('      %s = exp(%s);' % (value, tmp))


class SquareNoise(BasicNoiseSource):
    def __init__(self, noise, name=None):
        BasicNoiseSource.__init__(self, noise, name, 'square')

    def get_id(self):
        return 'square-' + self.noise.get_id()

    def noise_value(self, code, value, point):
        code.append('        {')
        code.append('          float tmp_square;')
        self.noise.noise_value(code, 'tmp_square', point)
        code.append('        %s = tmp_square * tmp_square;' % value)
        code.append('        }')


class CubeNoise(BasicNoiseSource):
    def __init__(self, noise, name=None):
        BasicNoiseSource.__init__(self, noise, name, 'cube')

    def get_id(self):
        return 'cube-' + self.noise.get_id()

    def noise_value(self, code, value, point):
        code.append('        {')
        code.append('          float tmp_cube;')
        self.noise.noise_value(code, 'tmp_cube', point)
        code.append('        %s = tmp_cube * tmp_cube * tmp_cube;' % value)
        code.append('        }')


class NoiseClamp(NoiseSource):
    def __init__(self, noise, min_value, max_value, dynamic=False, name=None, ranges={}):
        NoiseSource.__init__(self, name, 'clamp', ranges)
        self.noise = noise
        self.min_value = min_value
        self.max_value = max_value
        self.dynamic = dynamic

    def get_id(self):
        if self.dynamic:
            return 'clamp-' + self.noise.get_id()
        else:
            return ('clamp-%g-%g-' % (self.min_value, self.max_value)) + self.noise.get_id()

    def noise_uniforms(self, code):
        self.noise.noise_uniforms(code)
        if self.dynamic:
            code.append("uniform float %s_min;" % self.str_id)
            code.append("uniform float %s_max;" % self.str_id)

    def noise_extra(self, program, code):
        self.noise.noise_extra(program, code)

    def noise_func(self, code):
        self.noise.noise_func(code)
        code.append('float noise_clamp_%d(vec3 point)' % self.num_id)
        code.append('{')
        code.append('  float value;')
        self.noise.noise_value(code, 'value', 'point')
        if self.dynamic:
            code.append('  return clamp(value, %s_min, %s_max);' % (self.str_id, self.str_id))
        else:
            code.append('  return clamp(value, %g, %g);' % (self.min_value, self.max_value))
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_clamp_%d(%s);' % (value, self.num_id, point))

    def update(self, instance):
        self.noise.update(instance)
        if self.dynamic:
            instance.set_shader_input('%s_min' % self.str_id, self.min_value)
            instance.set_shader_input('%s_max' % self.str_id, self.max_value)

    def get_user_parameters(self):
        if not self.dynamic:
            return []
        group = ParametersGroup(self.name)
        group.add_parameters(
            AutoUserParameter(
                'Min',
                'min_value',
                self,
                param_type=AutoUserParameter.TYPE_FLOAT,
                value_range=self.ranges.get('min'),
            )
        )
        group.add_parameters(
            AutoUserParameter(
                'Max',
                'max_value',
                self,
                param_type=AutoUserParameter.TYPE_FLOAT,
                value_range=self.ranges.get('max'),
            )
        )
        return [group]


class NoiseMin(NoiseSource):
    def __init__(self, noise_a, noise_b, name=None):
        NoiseSource.__init__(self, name, 'min')
        self.noise_a = noise_a
        self.noise_b = noise_b

    def get_id(self):
        return self.noise_a.get_id() + "-min-" + self.noise_b.get_id()

    def noise_uniforms(self, code):
        self.noise_a.noise_uniforms(code)
        self.noise_b.noise_uniforms(code)

    def noise_extra(self, program, code):
        self.noise_a.noise_extra(program, code)
        self.noise_b.noise_extra(program, code)

    def noise_func(self, code):
        self.noise_a.noise_func(code)
        self.noise_b.noise_func(code)
        code.append('float noise_min_%d(vec3 point)' % self.num_id)
        code.append('{')
        code.append('  float value_a;')
        code.append('  float value_b;')
        self.noise_a.noise_value(code, 'value_a', 'point')
        self.noise_b.noise_value(code, 'value_b', 'point')
        code.append('  return min(value_a, value_b);')
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_min_%d(%s);' % (value, self.num_id, point))

    def update(self, instance):
        self.noise_a.update(instance)
        self.noise_b.update(instance)

    def get_user_parameters(self):
        return self.noise_a.get_user_parameters() + self.noise_b.get_user_parameters()


class NoiseMax(NoiseSource):
    def __init__(self, noise_a, noise_b, name=None):
        NoiseSource.__init__(self, name, 'max')
        self.noise_a = noise_a
        self.noise_b = noise_b

    def get_id(self):
        return self.noise_a.get_id() + "-max-" + self.noise_b.get_id()

    def noise_uniforms(self, code):
        self.noise_a.noise_uniforms(code)
        self.noise_b.noise_uniforms(code)

    def noise_extra(self, program, code):
        self.noise_a.noise_extra(program, code)
        self.noise_b.noise_extra(program, code)

    def noise_func(self, code):
        self.noise_a.noise_func(code)
        self.noise_b.noise_func(code)
        code.append('float noise_max_%d(vec3 point)' % self.num_id)
        code.append('{')
        code.append('  float value_a;')
        code.append('  float value_b;')
        self.noise_a.noise_value(code, 'value_a', 'point')
        self.noise_b.noise_value(code, 'value_b', 'point')
        code.append('  return max(value_a, value_b);')
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_max_%d(%s);' % (value, self.num_id, point))

    def update(self, instance):
        self.noise_a.update(instance)
        self.noise_b.update(instance)

    def get_user_parameters(self):
        return self.noise_a.get_user_parameters() + self.noise_b.get_user_parameters()
