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


class GpuNoiseLibPerlin3D(NoiseSource):
    def __init__(self, name=None):
        NoiseSource.__init__(self, name, 'gnl-perlin3d')

    def get_id(self):
        return 'gnl-perlin3d'

    def noise_extra(self, program, code):
        program.include(
            code,
            'gnl-FAST32_hash',
            defaultDirContext.find_shader("gpu-noise-lib/FAST32_hash.glsl"),
        )
        program.include(
            code,
            'gnl-Interpolation',
            defaultDirContext.find_shader("gpu-noise-lib/Interpolation.glsl"),
        )
        program.include(
            code,
            'gnl-Noise',
            defaultDirContext.find_shader("gpu-noise-lib/Perlin3D.glsl"),
        )

    def noise_value(self, code, value, point):
        code.append('        %s  = Perlin3D(%s);' % (value, point))


class GpuNoiseLibCellular3D(NoiseSource):
    def __init__(self, name=None):
        NoiseSource.__init__(self, name, 'gnl-cell3d')

    def get_id(self):
        return 'gnl-cell3d'

    def noise_extra(self, program, code):
        program.include(
            code,
            'gnl-FAST32_hash',
            defaultDirContext.find_shader("gpu-noise-lib/FAST32_hash.glsl"),
        )
        program.include(
            code,
            'gnl-Cellular',
            defaultDirContext.find_shader("gpu-noise-lib/Cellular.glsl"),
        )

    def noise_value(self, code, value, point):
        code.append('        %s  = sqrt(Cellular3D(%s));' % (value, point))


class GpuNoiseLibPolkaDot3D(NoiseSource):
    def __init__(self, min_radius, max_radius, name=None):
        NoiseSource.__init__(self, name, 'gnl-polkadot3d')
        self.min_radius = min_radius
        self.max_radius = max_radius

    def get_id(self):
        return 'gnl-polkadot3d'

    def noise_extra(self, program, code):
        program.include(
            code,
            'gnl-FAST32_hash',
            defaultDirContext.find_shader("gpu-noise-lib/FAST32_hash.glsl"),
        )
        program.include(
            code,
            'gnl-Falloff',
            defaultDirContext.find_shader("gpu-noise-lib/Falloff.glsl"),
        )
        program.include(
            code,
            'gnl-PolkaDot',
            defaultDirContext.find_shader("gpu-noise-lib/PolkaDot.glsl"),
        )

    def noise_value(self, code, value, point):
        code.append('        %s  = PolkaDot3D(%s, %g, %g);' % (value, point, self.min_radius, self.max_radius))
