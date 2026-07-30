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


class QuilezPerlin3D(NoiseSource):
    def __init__(self, name=None):
        NoiseSource.__init__(self, name, 'quilez-perlin3d')

    def get_id(self):
        return 'quilez-perlin3d'

    def noise_extra(self, program, code):
        program.include(
            code,
            'quilez-noise',
            defaultDirContext.find_shader("quilez/GradientNoise3D.glsl"),
        )

    def noise_value(self, code, value, point):
        code.append('        %s  = noise(%s);' % (value, point))


class QuilezGradientNoise3D(NoiseSource):
    def __init__(self, name=None):
        NoiseSource.__init__(self, name, 'quilez-gradientnoise3d')

    def get_id(self):
        return 'quilez-gradientnoise3d'

    def noise_extra(self, program, code):
        program.include(
            code,
            'quilez-noise',
            defaultDirContext.find_shader("quilez/GradientNoise.glsl"),
        )

    def noise_value(self, code, value, point):
        code.append('        %s  = noise(%s);' % (value, point))
