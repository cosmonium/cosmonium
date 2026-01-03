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


from ..shadernoise import BasicNoiseSource, NoiseSource


class NoiseMap(BasicNoiseSource):
    def __init__(
        self,
        noise,
        min_value=0.0,
        max_value=1.0,
        src_min_value=-1.0,
        src_max_value=1.0,
        name=None,
    ):
        BasicNoiseSource.__init__(self, noise, name, 'map')
        self.min_value = min_value
        self.max_value = max_value
        self.src_min_value = src_min_value
        self.src_max_value = src_max_value
        self.range = self.max_value - self.min_value
        self.src_range = self.src_max_value - self.src_min_value
        self.range_factor = self.range / self.src_range

    def get_id(self):
        return 'map-%g-%g-' % (self.min_value, self.max_value) + self.noise.get_id()

    def noise_func(self, code):
        self.noise.noise_func(code)
        code.append('float noise_map_%d(vec3 point)' % self.num_id)
        code.append('{')
        code.append('  float value;')
        self.noise.noise_value(code, 'value', 'point')
        code.append(
            '  return clamp((value - %g) * %g + %g, %f, %f);'
            % (
                self.src_min_value,
                self.range_factor,
                self.min_value,
                self.min_value,
                self.max_value,
            )
        )
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_map_%d(%s);' % (value, self.num_id, point))


class RidgedNoise(BasicNoiseSource):
    def __init__(self, noise, offset=0.33, shift=True, name=None):
        BasicNoiseSource.__init__(self, noise, name, 'ridged')
        self.offset = offset
        self.shift = shift

    def get_id(self):
        return 'ridged-' + self.noise.get_id()

    def noise_value(self, code, value, point):
        code.append('        {')
        code.append('          float tmp_ridged;')
        self.noise.noise_value(code, 'tmp_ridged', point)
        if self.shift:
            code.append('        %s  = (1.0 - abs(tmp_ridged) - %g) * 2.0 - 1.0;' % (value, self.offset))
        else:
            code.append('        %s  = (1.0 - abs(tmp_ridged) - %g);' % (value, self.offset))
        code.append('        }')


class NoiseThreshold(NoiseSource):
    def __init__(self, noise_a, noise_b, name=None):
        NoiseSource.__init__(self, name, 'threshold')
        self.noise_a = noise_a
        self.noise_b = noise_b

    def get_id(self):
        return self.noise_a.get_id() + "-threshold-" + self.noise_b.get_id()

    def noise_uniforms(self, code):
        self.noise_a.noise_uniforms(code)
        self.noise_b.noise_uniforms(code)

    def noise_extra(self, program, code):
        self.noise_a.noise_extra(program, code)
        self.noise_b.noise_extra(program, code)

    def noise_func(self, code):
        self.noise_a.noise_func(code)
        self.noise_b.noise_func(code)
        code.append('float noise_threshold_%d(vec3 point)' % self.num_id)
        code.append('{')
        code.append('  float value_a;')
        code.append('  float value_b;')
        self.noise_a.noise_value(code, 'value_a', 'point')
        self.noise_b.noise_value(code, 'value_b', 'point')
        code.append('  return max((value_a - value_b), 0.0);')
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = noise_threshold_%d(%s);' % (value, self.num_id, point))

    def update(self, instance):
        self.noise_a.update(instance)
        self.noise_b.update(instance)

    def get_user_parameters(self):
        return self.noise_a.get_user_parameters() + self.noise_b.get_user_parameters()
