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


class NoiseConst(NoiseSource):
    def __init__(self, value, dynamic=False, name=None, ranges={}):
        NoiseSource.__init__(self, name, 'const', ranges)
        self.value = value
        self.dynamic = dynamic

    def get_id(self):
        if self.dynamic:
            return 'const'
        else:
            return '%g' % self.value

    def noise_uniforms(self, code):
        if self.dynamic:
            code.append("uniform float %s;" % self.str_id)

    def noise_value(self, code, value, point):
        if self.dynamic:
            code.append('        %s  = %s;' % (value, self.str_id))
        else:
            code.append('        %s  = %g;' % (value, self.value))

    def update(self, instance):
        if self.dynamic:
            instance.set_shader_input('%s' % self.str_id, self.value)

    def get_user_parameters(self):
        if not self.dynamic:
            return []
        group = ParametersGroup(self.name)
        group.add_parameters(
            AutoUserParameter(
                'value',
                'value',
                self,
                param_type=AutoUserParameter.TYPE_FLOAT,
                value_range=self.ranges.get('value'),
            )
        )
        return [group]


class NoiseCoord(NoiseSource):
    def __init__(self, coord, name=None):
        NoiseSource.__init__(self, name, 'coord')
        self.coord = coord

    def get_id(self):
        return '%s' % self.coord

    def noise_value(self, code, value, point):
        code.append('        %s  = %s.%s;' % (value, point, self.coord))
