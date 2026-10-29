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

from ..component import ShaderComponent
from .base import ShaderShadowInterface


class ShaderSphereShadow(ShaderComponent, ShaderShadowInterface):
    fragment_requires = {'world_vertex'}

    def __init__(self, max_occluders, far_sun, oblate_occluder):
        ShaderComponent.__init__(self)
        self.max_occluders = max_occluders
        self.far_sun = far_sun
        self.oblate_occluder = oblate_occluder

    def get_id(self):
        name = "ss"
        if self.oblate_occluder:
            name += "o"
        return name

    def fragment_uniforms(self, code):
        code.append("uniform vec3 star_center;")
        code.append("uniform float star_radius;")
        if self.far_sun:
            code.append("uniform float star_ar;")
        code.append("uniform vec3 occluder_centers[%d];" % self.max_occluders)
        code.append("uniform float occluder_radii[%d];" % self.max_occluders)
        if self.oblate_occluder:
            code.append("uniform mat4 occluder_transform[%d];" % self.max_occluders)
        code.append("uniform int nb_of_occluders;")

    def shadow_for(self, code, light, light_direction, eye_light_direction):
        code.append("for (int i = 0; i < nb_of_occluders; i++) {")
        if self.oblate_occluder:
            code.append(
                "  vec3 scaled_world_vertex = "
                "occluder_centers[i] + mat3(occluder_transform[i]) * (world_vertex - occluder_centers[i]);"
            )
            code.append(
                "  vec3 scaled_star_center = "
                "occluder_centers[i] + mat3(occluder_transform[i]) * (star_center - occluder_centers[i]);"
            )
        else:
            code.append("  vec3 scaled_world_vertex = world_vertex;")
            code.append("  vec3 scaled_star_center = star_center;")
        code.append("  vec3 star_local = scaled_star_center - scaled_world_vertex;")
        if not self.far_sun:
            # Small angle approximation
            code.append("  float star_ar = star_radius / length(star_local);")
        code.append("  vec3 occluder_local = occluder_centers[i] - scaled_world_vertex;")
        code.append("  float occluder_radius = occluder_radii[i];")
        # Small angle approximation
        code.append("  float occluder_ar = occluder_radius / length(occluder_local);")
        code.append("  float ab = dot(star_local, occluder_local);")
        code.append("  if (ab > 0) {")
        code.append("    //Apply shadow only if the occluder is between the target and the star")
        # acos(dot) has precision issues and shows artefacts in the penumbra
        # We use asin(cross()) instead to diminish the artifacts
        code.append(
            "      float separation = "
            "asin(clamp(length(cross(normalize(star_local), normalize(occluder_local))), 0, 1));"
        )
        code.append("    if (separation > star_ar + occluder_ar) {")
        code.append("      // No overlap")
        code.append("    } else if (separation <= abs(occluder_ar - star_ar)) {")
        code.append("      if (occluder_ar > star_ar) {")
        code.append("        // Full overlap")
        code.append("        global_shadow = 0.0;")
        code.append("      } else {")
        code.append("        // Occluder fully inside star, attenuation is the ratio of the visible surfaces")
        code.append("        float surface_ratio = clamp((occluder_ar * occluder_ar) / (star_ar * star_ar), 0, 1);")
        code.append("        global_shadow *= 1.0 - surface_ratio;")
        code.append("      }")
        code.append("    } else {")
        code.append("      // Occluder partially occluding star, use linear approximation")
        code.append("      float surface_ratio = clamp((occluder_ar * occluder_ar) / (star_ar * star_ar), 0, 1);")
        code.append("      float ar_diff = abs(star_ar - occluder_ar);")
        code.append(
            "      global_shadow *= "
            "1.0 - surface_ratio * (1.0 - clamp((separation - ar_diff) / (star_ar + occluder_ar - ar_diff), 0, 1));"
        )
        code.append("      }")
        code.append("  } else {")
        code.append("    //Not in shadow")
        code.append("  }")
        code.append("}")


class ShaderSphereSelfShadow(ShaderComponent, ShaderShadowInterface):
    # TODO: Until proper self-shadowing is added, the effect of the normal map
    # is damped by this factor when the angle between the normal and the light
    # is negative (angle > 90deg)
    fake_self_shadow = 0.05

    def get_id(self):
        return 'sssn' if self.appearance.has_normal else 'sss'

    def shadow_for(self, code, light, light_direction, eye_light_direction):
        if self.appearance.has_normal:
            code.append(f"float terminator_coef = dot(shape_eye_normal, {eye_light_direction});")
            code.append(
                "global_shadow *= smoothstep(0.0, 1.0, (%f + terminator_coef) * %f);"
                % (self.fake_self_shadow, 1.0 / self.fake_self_shadow)
            )
