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
from ..shadernoise import BasicNoiseSource


class SpiralNoise(BasicNoiseSource):
    def __init__(
        self,
        noise,
        octaves=8,
        frequency=1.0,
        lacunarity=2.0,
        gain=0.5,
        nudge=0.5,
        name=None,
        ranges={},
    ):
        BasicNoiseSource.__init__(self, noise, name, 'spiral', ranges)
        self.octaves = octaves
        self.frequency = frequency
        self.lacunarity = lacunarity
        self.gain = gain
        self.nudge = nudge

    def get_id(self):
        return self.str_id + '-' + self.noise.get_id()

    def noise_uniforms(self, code):
        self.noise.noise_uniforms(code)
        code += [
            "uniform float %s_octaves;" % self.str_id,
            "uniform float %s_frequency;" % self.str_id,
            "uniform float %s_lacunarity;" % self.str_id,
            "uniform float %s_amplitude;" % self.str_id,
            "uniform float %s_gain;" % self.str_id,
            "uniform float %s_nudge;" % self.str_id,
        ]

    def noise_func(self, code):
        self.noise.noise_func(code)
        code.append('float Spiral_%s(vec3 point)' % self.str_id)
        code.append('{')
        code.append("    float nudge = %s_nudge;" % self.str_id)
        code.append("    float normalizer = 1.0 / sqrt(1.0 + nudge*nudge);")
        code.append("    float frequency = %s_frequency;" % self.str_id)
        code.append("    float lacunarity = %s_lacunarity;" % self.str_id)
        code.append("    float gain = %s_gain;" % self.str_id)
        code.append('    float result = 0.0;')
        code.append('    float amplitude = 1.0;')
        code.append('    float max_value = 0.0;')
        code.append('    for (int i = 0; i < %s_octaves; ++i)' % self.str_id)
        code.append('    {')
        code.append('        float value;')
        self.noise.noise_value(code, 'value', 'point * frequency')
        code.append('        result += value * amplitude;')
        code.append('        max_value += amplitude;')
        code.append('        amplitude *= gain;')
        code.append('        frequency *= lacunarity;')
        code.append('        point.xy += vec2(point.y, -point.x) * nudge;')
        code.append('        point.xy *= normalizer;')
        code.append('        point.xz += vec2(point.z, -point.x) * nudge;')
        code.append('        point.xz *= normalizer;')
        code.append('    }')
        code.append('    return result / max_value;')
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = Spiral_%s(%s);' % (value, self.str_id, point))

    def update(self, instance):
        self.noise.update(instance)
        instance.set_shader_input('%s_octaves' % self.str_id, self.octaves)
        instance.set_shader_input('%s_frequency' % self.str_id, self.frequency)
        instance.set_shader_input('%s_lacunarity' % self.str_id, self.lacunarity)
        instance.set_shader_input('%s_gain' % self.str_id, self.gain)
        instance.set_shader_input('%s_nudge' % self.str_id, self.nudge)

    def get_user_parameters(self):
        group = ParametersGroup(
            self.name,
            AutoUserParameter(
                'Octaves',
                'octaves',
                self,
                AutoUserParameter.TYPE_INT,
                value_range=self.ranges.get('octaves'),
            ),
            AutoUserParameter(
                'Frequency',
                'frequency',
                self,
                AutoUserParameter.TYPE_FLOAT,
                value_range=self.ranges.get('frequency'),
            ),
            AutoUserParameter(
                'Lacunarity',
                'lacunarity',
                self,
                AutoUserParameter.TYPE_FLOAT,
                value_range=self.ranges.get('lacunarity'),
            ),
            AutoUserParameter(
                'Gain',
                'gain',
                self,
                AutoUserParameter.TYPE_FLOAT,
                value_range=self.ranges.get('gain'),
            ),
            AutoUserParameter(
                'Nudge',
                'nudge',
                self,
                AutoUserParameter.TYPE_FLOAT,
                value_range=self.ranges.get('nudge'),
            ),
        )
        group.add_parameters(self.noise.get_user_parameters())
        return [group]
