#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2023 Laurent Deru.
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

from __future__ import annotations

from ...shaders.component import ShaderComponent


class LuminanceThresholdFragmentShader(ShaderComponent):

    def get_id(self) -> str:
        return 'luminance-threshold'

    def fragment_uniforms(self, code: list[str]) -> None:
        code.append('uniform float max_luminance;')

    def fragment_shader(self, code: list[str]) -> None:
        code.append('  float luminance = dot(pixel_color, vec3(0.2126, 0.7152, 0.0722));')
        code.append('  if (luminance > max_luminance) {')
        code.append('    result = pixel_color;')
        code.append('  } else {')
        code.append('    result = vec3(0.0);')
        code.append('  }')
