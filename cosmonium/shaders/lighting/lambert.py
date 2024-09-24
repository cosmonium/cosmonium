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
from .base import BRDFInterface


class LambertPhongLightingModel(ShaderComponent, BRDFInterface):

    fragment_requires = {'eye_vertex', 'eye_normal'}

    def get_id(self):
        return "lambert"

    def lambert_phong_material(self, code):
        code.append("struct LambertPhongMaterial")
        code.append("{")
        code.append("    vec3 diffuse_color;")
        if self.appearance.has_specular:
            code.append("    vec3 specular_color;")
            code.append("    float shininess;")
        code.append("};")

    def lambert_phong_vectors(self, code):
        code.append("struct LambertPhongVectors")
        code.append("{")
        if self.appearance.has_specular:
            code.append("    float n_dot_h;")
        code.append("    float n_dot_l;")
        code.append("};")

    def lambert_phong_calc_vectors(self, code):
        code.append("LambertPhongVectors calc_lambert_phong_vectors(vec3 normal, vec3 obs_dir, vec3 light_dir)")
        code.append("{")
        code.append("    float n_dot_l = min(dot(normal, light_dir), 1.0);")
        if self.appearance.has_specular:
            code.append("    vec3 half_vec = normalize(light_dir + obs_dir);")
            code.append("    float n_dot_h = clamp(dot(normal, half_vec), 0.0, 1.0);")
        code.append("    return LambertPhongVectors(")
        if self.appearance.has_specular:
            code.append("        n_dot_h,")
        code.append("        n_dot_l")
        code.append("    );")
        code.append("}")

    def lambert_phong_brdf(self, code):
        code.append(
            "vec3 lambert_phong_brdf("
            "in LambertPhongMaterial material, "
            "in LambertPhongVectors vectors, "
            "in vec3 light_direction, "
            "in vec3 light_color) {"
        )
        code.append("  vec3 contribution = vec3(0);")
        code.append("  if (vectors.n_dot_l > 0.0) {")
        if self.appearance.has_specular:
            code.append("    vec3 specular = light_color * pow(vectors.n_dot_h, material.shininess);")
            code.append("    contribution += specular * material.specular_color;")
        code.append("    float diffuse_coef = clamp(vectors.n_dot_l, 0.0, 1.0);")
        code.append("    contribution += light_color * diffuse_coef * material.diffuse_color;")
        code.append("  }")
        code.append("  return contribution;")
        code.append("}")

    def fragment_extra(self, code):
        self.lambert_phong_material(code)
        self.lambert_phong_vectors(code)
        self.lambert_phong_calc_vectors(code)
        self.lambert_phong_brdf(code)

    def prepare_material(self, code):
        code.append("  LambertPhongMaterial material;")
        code.append("  material.diffuse_color = surface_color.rgb;")
        if self.appearance.has_specular:
            code.append("  material.specular_color = specular_color.rgb;")
            code.append("  material.shininess = shininess;")
            code.append("  vec3 obs_dir = normalize(-eye_vertex);")
        else:
            code.append("  vec3 obs_dir = vec3(0);")

    def light_contribution(self, code, result, light_direction, light_color):
        code.append(
            f"    LambertPhongVectors vectors = calc_lambert_phong_vectors(eye_normal, obs_dir, {light_direction});"
        )
        code.append(f"    {result} = lambert_phong_brdf(material, vectors, {light_direction}, {light_color}.rgb);")

    def ambient_contribution(self, code, result, ambient_diffuse):
        code.append(f"    {result} = material.diffuse_color * {ambient_diffuse}.rgb;")

    def cos_light_normal(self):
        return "vectors.n_dot_l"
