#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
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
        code.append('uniform float bloom_threshold;')
        code.append('uniform float bloom_knee;')

    def fragment_shader(self, code: list[str]) -> None:
        code.append('  float luminance = dot(pixel_color, vec3(0.2126, 0.7152, 0.0722));')
        code.append('  float soft = min(')
        code.append('      max(0, luminance - bloom_threshold + bloom_threshold * bloom_knee),')
        code.append('      2 *  bloom_threshold * bloom_knee);')
        code.append('  soft = soft * soft / (4 * bloom_threshold * bloom_knee + 1e-9);')
        code.append('  float weight = max(soft, luminance - bloom_threshold) / max(luminance, 1e-9);')
        code.append('  result = pixel_color * weight;')
