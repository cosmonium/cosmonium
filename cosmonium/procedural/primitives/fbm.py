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
from ..shadernoise import BasicNoiseSource


class FbmNoise(BasicNoiseSource):
    def __init__(
        self,
        noise,
        octaves=8,
        frequency=1.0,
        lacunarity=2.0,
        geometric=True,
        h=0.25,
        gain=0.5,
        name=None,
        ranges={},
    ):
        BasicNoiseSource.__init__(self, noise, name, 'fbm', ranges)
        self.octaves = octaves
        self.frequency = frequency
        self.lacunarity = lacunarity
        self.geometric = geometric
        self.h = h
        self.gain = gain

    def get_id(self):
        if self.geometric:
            geom = '-g'
        else:
            geom = ''
        return self.str_id + geom + '-' + self.noise.get_id()

    def noise_uniforms(self, code):
        BasicNoiseSource.noise_uniforms(self, code)
        code += [
            "uniform float %s_octaves;" % self.str_id,
            "uniform float %s_frequency;" % self.str_id,
            "uniform float %s_lacunarity;" % self.str_id,
            "uniform float %s_amplitude;" % self.str_id,
        ]
        if self.geometric:
            code.append("uniform float %s_gain;" % self.str_id)
        else:
            code.append("uniform float %s_h;" % self.str_id)

    def noise_func(self, code):
        self.noise.noise_func(code)
        code.append('float Fbm_%s(vec3 point)' % self.str_id)
        code.append('{')
        code.append("float frequency = %s_frequency;" % self.str_id)
        if self.geometric:
            code.append("float gain = %s_gain;" % self.str_id)
        else:
            code.append("float gain = pow(%s_lacunarity, -%s_h);" % (self.str_id, self.str_id))
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
        code.append('        frequency *= %s_lacunarity;' % self.str_id)
        code.append('    }')
        code.append('    return result / max_value;')
        code.append('}')

    def noise_value(self, code, value, point):
        code.append('%s = Fbm_%s(%s);' % (value, self.str_id, point))

    def update(self, instance):
        self.noise.update(instance)
        instance.set_shader_input('%s_octaves' % self.str_id, self.octaves)
        instance.set_shader_input('%s_frequency' % self.str_id, self.frequency)
        instance.set_shader_input('%s_lacunarity' % self.str_id, self.lacunarity)
        if self.geometric:
            instance.set_shader_input('%s_gain' % self.str_id, self.gain)
        else:
            instance.set_shader_input('%s_h' % self.str_id, self.h)

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
        )
        group.add_parameters(self.noise.get_user_parameters())
        return [group]
