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


from .base import GeometryControl


class WideLineGeometryControl(GeometryControl):
    """Geometry control that expands line segments into camera-facing quads.

    This component contributes to three shader stages:
    - Vertex shader: passes per-vertex fade values through to the geometry shader.
    - Geometry shader: expands line segments into screen-aligned quads with
      near-plane clipping and per-pixel line coordinates.
    - Fragment shader: declares the inputs produced by the geometry shader
      (geom_color, line_coord, line_fade).
    """

    def __init__(self, enable_fade: bool = True):
        GeometryControl.__init__(self)
        self.enable_fade = enable_fade

    def get_id(self):
        base = "wlgc"
        if self.enable_fade:
            base += "-fade"
        return base

    # -- Vertex shader contributions (passed through to geometry shader) --

    def vertex_inputs(self, code):
        if self.enable_fade:
            code.append('in float fade;')

    def vertex_outputs(self, code):
        if self.enable_fade:
            code.append('out float vertex_fade;')

    def vertex_shader(self, code):
        if self.enable_fade:
            code.append("vertex_fade = fade;")

    # -- Fragment shader contributions (inputs from geometry shader outputs) --

    def fragment_inputs(self, code):
        code.append("noperspective in vec4 geom_color;")
        code.append("noperspective in vec2 line_coord;")
        if self.enable_fade:
            code.append("noperspective in float line_fade;")

    # -- Geometry shader contributions --

    def geometry_layout(self, code):
        code.append("layout(lines) in;")
        code.append("layout(triangle_strip, max_vertices=4) out;")

    def geometry_uniforms(self, code):
        code.append(
            """
uniform vec2 win_size;
// wide_line_parameters: .x=unused, .y=unused, .z=unused, .w=halo_expansion_px
uniform vec4 wide_line_parameters;
"""
        )

    def geometry_inputs(self, code):
        code.append(
            """
in vec4 vertex_color[];
"""
        )
        if self.enable_fade:
            code.append(
                """
// Fade value per vertex (0.0 = fully transparent, 1.0 = fully opaque)
in float vertex_fade[];
"""
            )

    def geometry_outputs(self, code):
        code.append(
            """
noperspective out vec4 geom_color;
// line_coord.y: signed distance from line centre in screen pixels
//   (negative = one side, positive = other side)
noperspective out vec2 line_coord;
"""
        )
        if self.enable_fade:
            code.append(
                """
// Fade value along line length
noperspective out float line_fade;
"""
            )

    def geometry_shader(self, code):
        code.append(
            """
    // Get line endpoints in clip space
    vec4 p0_clip = gl_in[0].gl_Position;
    vec4 p1_clip = gl_in[1].gl_Position;

    // Near plane clipping
    float near_threshold = 1e-6;

    bool p0_behind = p0_clip.w < near_threshold;
    bool p1_behind = p1_clip.w < near_threshold;

    if (p0_behind && p1_behind) { return; }

    vec4 color0 = vertex_color[0];
    vec4 color1 = vertex_color[1];
"""
        )
        if self.enable_fade:
            code.append("    float fade0 = vertex_fade[0];")
            code.append("    float fade1 = vertex_fade[1];")

        code.append(
            """
    // Clip line segment against near plane if one endpoint is behind the camera.
    // Disabled as there is no visual gain.
    if (false && (p0_behind || p1_behind)) {
        float t = (near_threshold - p0_clip.w) / (p1_clip.w - p0_clip.w);
        t = clamp(t, 0.0, 1.0);
        vec4 p_clipped = mix(p0_clip, p1_clip, t);
        p_clipped.w = near_threshold;
        if (p0_behind) {
            p0_clip = p_clipped;
            color0 = mix(color0, color1, t);
"""
        )
        if self.enable_fade:
            code.append("            fade0 = mix(fade0, fade1, t);")
        code.append(
            """
        } else {
            p1_clip = p_clipped;
            color1 = mix(color0, color1, t);
"""
        )
        if self.enable_fade:
            code.append("            fade1 = mix(fade0, fade1, t);")
        code.append(
            """
        }
    }

    vec2 p0_ndc = p0_clip.xy / p0_clip.w;
    vec2 p1_ndc = p1_clip.xy / p1_clip.w;

    vec2 p0_screen = (p0_ndc + vec2(1.0)) * 0.5 * win_size;
    vec2 p1_screen = (p1_ndc + vec2(1.0)) * 0.5 * win_size;

    vec2 line_delta = p1_screen - p0_screen;
    float line_length = length(line_delta);
    if (line_length <= 0) { return; }

    vec2 line_dir  = line_delta / line_length;
    vec2 line_perp = vec2(-line_dir.y, line_dir.x);

    // Core half-width in screen pixels
    float core_half_px = wide_line_parameters.x * 0.5;
    // Halo expansion pre-computed by the caller and stored in .w
    float total_half_px = core_half_px + wide_line_parameters.w;

    vec2 offset_screen = line_perp * total_half_px;
    vec2 offset_ndc    = offset_screen / (win_size * 0.5);

    // line_coord.y carries the signed distance from centre in SCREEN PIXELS.

    gl_Position = vec4((p0_ndc - offset_ndc) * p0_clip.w, p0_clip.z, p0_clip.w);
    geom_color = color0;
    line_coord = vec2(0.0, -total_half_px);
"""
        )
        if self.enable_fade:
            code.append("    line_fade = fade0;")

        code.append(
            """
    EmitVertex();

    gl_Position = vec4((p0_ndc + offset_ndc) * p0_clip.w, p0_clip.z, p0_clip.w);
    geom_color = color0;
    line_coord = vec2(0.0,  total_half_px);
"""
        )
        if self.enable_fade:
            code.append("    line_fade = fade0;")

        code.append(
            """
    EmitVertex();

    gl_Position = vec4((p1_ndc - offset_ndc) * p1_clip.w, p1_clip.z, p1_clip.w);
    geom_color = color1;
    line_coord = vec2(1.0, -total_half_px);
"""
        )
        if self.enable_fade:
            code.append("    line_fade = fade1;")

        code.append(
            """
    EmitVertex();

    gl_Position = vec4((p1_ndc + offset_ndc) * p1_clip.w, p1_clip.z, p1_clip.w);
    geom_color = color1;
    line_coord = vec2(1.0,  total_half_px);
"""
        )
        if self.enable_fade:
            code.append("    line_fade = fade1;")
        code.append("    EmitVertex();")
        code.append("    EndPrimitive();")
