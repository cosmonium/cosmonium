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


from .base import LightingModelBase


class SmoothLineLightingModel(LightingModelBase):

    def __init__(self, enable_fade: bool = False):
        """
        Initialize the smooth line lighting model.

        Args:
            enable_fade: When True, line fade is enabled, allowing per-vertex fade values.
        """
        super().__init__()
        self.enable_fade = enable_fade

    def get_id(self):
        base = "sl"
        if self.enable_fade:
            base += "-fade"
        return base

    def vertex_outputs(self, code):
        code.append('noperspective out vec2 line_center;')
        if self.enable_fade:
            code.append('noperspective out float vertex_fade_sl;')

    def vertex_inputs(self, code):
        if self.enable_fade:
            code.append('in float fade;')

    def fragment_inputs(self, code):
        code.append("noperspective in vec2 line_center;")
        if self.enable_fade:
            code.append("noperspective in float vertex_fade_sl;")

    def fragment_uniforms(self, code):
        code.append("uniform vec2 line_parameters;")

    def vertex_shader(self, code):
        # code.append("vec4 proj_vertex4 = p3d_ProjectionMatrix * (p3d_ModelViewMatrix * model_vertex4);")
        code.append("line_center = vec2(0.5) * (gl_Position.xy / gl_Position.w + vec2(1)) * win_size;")
        if self.enable_fade:
            code.append("vertex_fade_sl = fade;")

    def fragment_shader(self, code):
        if self.appearance.has_surface:
            code.append("total_diffuse_color = surface_color;")
            code.append("float distance = length(line_center - gl_FragCoord.xy);")
            code.append("if (distance > line_parameters.x) {")
            code.append("  total_diffuse_color = vec4(0);")
            code.append("} else {")
            code.append(
                "  total_diffuse_color *= pow((line_parameters.x - distance) / line_parameters.x, line_parameters.y);"
            )
            if self.enable_fade:
                code.append("  total_diffuse_color *= vertex_fade_sl;")
            code.append("}")
