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


from ...dircontext import defaultDirContext
from ..shadernoise import NoiseSource


class SteGuPerlin3D(NoiseSource):
    def __init__(self, name=None):
        NoiseSource.__init__(self, name, 'stegu-perlin3d')

    def get_id(self):
        return 'stegu-perlin3d'

    def noise_extra(self, program, code):
        program.include(code, 'stegu-common', defaultDirContext.find_shader("stegu/common.glsl"))
        program.include(code, 'stegu-snoise', defaultDirContext.find_shader("stegu/noise3D.glsl"))

    def noise_value(self, code, value, point):
        code.append('        %s  = snoise(%s);' % (value, point))


class SteGuCellular3D(NoiseSource):
    def __init__(self, fast, name=None, prefix='stegu-cellular3d'):
        NoiseSource.__init__(self, name, prefix)
        self.fast = fast

    def get_id(self):
        if self.fast:
            return 'stegu-cellular3d-fast'
        else:
            return 'stegu-cellular3d'

    def noise_extra(self, program, code):
        program.include(code, 'stegu-common', defaultDirContext.find_shader("stegu/common.glsl"))
        if self.fast:
            program.include(
                code,
                'stegu-cellular',
                defaultDirContext.find_shader("stegu/cellular2x2x2.glsl"),
            )
        else:
            program.include(
                code,
                'stegu-cellular',
                defaultDirContext.find_shader("stegu/cellular3D.glsl"),
            )

    def noise_value(self, code, value, point):
        if self.fast:
            code.append('        %s = cellular2x2x2(%s).x;' % (value, point))
        else:
            code.append('        %s = cellular(%s).x;' % (value, point))


class SteGuCellularDiff3D(SteGuCellular3D):
    def __init__(self, fast, name=None):
        SteGuCellular3D.__init__(self, fast, name, 'stegu-cellular3d-diff')

    def get_id(self):
        return SteGuCellular3D.get_id(self) + '-diff'

    def noise_value(self, code, value, point):
        if self.fast:
            code.append('        vec2 F = cellular2x2x2(%s);' % (point))
        else:
            code.append('        vec2 F = cellular(%s);' % (point))
        code.append('        %s  = F.y - F.x;' % (value))
