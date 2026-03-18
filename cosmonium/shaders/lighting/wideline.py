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


from ...utils import TransparencyBlend
from .base import LightingModelBase


class WideLineLightingModel(LightingModelBase):
    """
    Lighting model for wide lines rendered via geometry shader expansion.

    This model supports two modes:
    - Glow mode (glow_mode=True): simulates a neon-tube glow with brightness
      peaking at the centre and decaying exponentially outward through both the core and the halo.
    - AA-only mode (glow_mode=False): renders a flat opaque core with a smooth
      anti-aliased edge, without any glow effect.

    Expected shader uniforms:
    - wide_line_parameters: vec4 where
        .x = width (total line width in pixels)
        .y = glow_intensity (multiplier for glow brightness, 0 to disable glow)
        .z = glow_falloff (controls how quickly glow decays with distance in pixels)
        .w = unused
    """

    def __init__(
        self,
        blend_mode: TransparencyBlend = TransparencyBlend.TB_Alpha,
        glow_mode: bool = False,
        enable_fade: bool = False,
    ):
        """
        Initialize the wide line lighting model.

        Args:
            blend_mode: Alpha blending mode for the line.
            glow_mode: When True  — neon-tube glow: brightness peaks at the centre and decays
                exponentially outward through both the core and the halo.
                When False — AA-only: flat opaque core with a smoothstep anti-aliased
                edge.
            enable_fade: When True, line fade is enabled, allowing per-vertex fade values.
        """
        super().__init__()
        self.blend_mode = blend_mode
        self.glow_mode = glow_mode
        self.enable_fade = enable_fade

    def get_id(self):
        base = "wl-glow" if self.glow_mode else "wl-aa"
        if self.enable_fade:
            base += "-fade"
        return base

    def fragment_uniforms(self, code):
        # wide_line_parameters: .x=width, .y=glow_intensity, .z=glow_falloff, .w=unused
        code.append("uniform vec4 wide_line_parameters;")

    def fragment_shader(self, code):
        if self.glow_mode:
            code.append(
                """
    total_diffuse_color = geom_color;

    // dist_px: distance from line centre in screen pixels
    float dist_px = abs(line_coord.y);

    // half_core_width: distance from line centre to core edge in pixels (half of the total core width)
    float half_core_width = wide_line_parameters.x * 0.5;

    float glow_intensity  = wide_line_parameters.y;
    float glow_falloff_px = max(wide_line_parameters.z, 0.001);

    // Neon-tube brightness: continuous exponential from centre outward (in pixels).
    // Centre (dist_px=0) is the hottest point; decays through core and halo.
    float full_glow = glow_intensity * exp(-dist_px / glow_falloff_px);

    // Alpha: flat opaque inside the core, exponential halo beyond the core edge.
    float halo_dist_px = max(dist_px - half_core_width, 0.0);
    float glow_alpha   = glow_intensity * exp(-halo_dist_px / glow_falloff_px);
    // Antialiasing for the core edge: smooth transition over 1 pixel straddling the core boundary.
    float core_alpha = smoothstep(half_core_width + 0.5, half_core_width - 0.5, dist_px);
    float final_alpha  = max(core_alpha, glow_alpha);

    total_diffuse_color.rgb = geom_color.rgb * (1.0 + full_glow);
"""
            )
        else:
            code.append(
                """
    total_diffuse_color = geom_color;

    // dist_px: distance from line centre in screen pixels
    float dist_px = abs(line_coord.y);

    // half_core_width: distance from line centre to core edge in pixels (half of the total core width)
    float half_core_width = wide_line_parameters.x * 0.5;

    // Smooth AA transition over exactly 1 pixel straddling the core edge.
    float core_edge = half_core_width;
    float final_alpha = smoothstep(core_edge + 0.5, core_edge - 0.5, dist_px);
"""
            )
        if self.enable_fade:
            code.append("    final_alpha *= line_fade;")
        if self.blend_mode == TransparencyBlend.TB_Additive:
            code.append("    total_diffuse_color.rgb *= final_alpha;")
            code.append("    total_diffuse_color.a = 1.0;")
        elif self.blend_mode == TransparencyBlend.TB_Alpha:
            code.append("    total_diffuse_color.a *= final_alpha;")
        elif self.blend_mode == TransparencyBlend.TB_PremultipliedAlpha:
            code.append("    total_diffuse_color.rgb *= final_alpha;")
            code.append("    total_diffuse_color.a *= final_alpha;")
