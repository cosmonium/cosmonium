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


class OrenNayarPhongLightingModel(ShaderComponent, BRDFInterface):

    fragment_requires = {'eye_vertex', 'eye_normal'}

    def get_id(self):
        return "oren-nayar"

    def fragment_uniforms(self, code):
        code.append("uniform float roughness_squared;")

    def oren_nayar_material(self, code):
        code.append("struct OrenNayarMaterial")
        code.append("{")
        code.append("    vec3 diffuse_color;")
        if self.appearance.has_specular:
            code.append("    vec3 specular_color;")
            code.append("    float shininess;")
        code.append("    float roughness_squared;")
        code.append("};")

    def oren_nayar_vectors(self, code):
        code.append("struct OrenNayarVectors")
        code.append("{")
        if self.appearance.has_specular:
            code.append("    float n_dot_h;")
        code.append("    float n_dot_l;")
        code.append("    float n_dot_v;")
        code.append("    vec3 normal;")
        code.append("    vec3 obs_dir;")
        code.append("    vec3 light_dir;")
        code.append("};")

    def oren_nayar_calc_vectors(self, code):
        code.append("OrenNayarVectors calc_oren_nayar_vectors(vec3 normal, vec3 obs_dir, vec3 light_dir)")
        code.append("{")
        code.append("    float n_dot_l = min(dot(normal, light_dir), 1.0);")
        code.append("    float n_dot_v = dot(obs_dir, normal);")
        if self.appearance.has_specular:
            code.append("    vec3 half_vec = normalize(light_dir + obs_dir);")
            code.append("    float n_dot_h = clamp(dot(normal, half_vec), 0.0, 1.0);")
        code.append("    return OrenNayarVectors(")
        if self.appearance.has_specular:
            code.append("        n_dot_h,")
        code.append("        n_dot_l,")
        code.append("        n_dot_v,")
        code.append("        normal,")
        code.append("        obs_dir,")
        code.append("        light_dir")
        code.append("    );")
        code.append("}")

    def oren_nayar_brdf(self, code):
        code.append(
            "vec3 oren_nayar_brdf("
            "in OrenNayarMaterial material, "
            "in OrenNayarVectors vectors, "
            "in vec3 light_direction, "
            "in vec3 light_color) {"
        )
        code.append("  vec3 contribution = vec3(0);")
        code.append("  if (vectors.n_dot_l > 0.0) {")
        if self.appearance.has_specular:
            code.append("    vec3 specular = light_color * pow(vectors.n_dot_h, material.shininess);")
            code.append("    contribution += specular * specular_factor.rgb * material.specular_color;")
        code.append("    float theta_r = acos(vectors.n_dot_v);")
        code.append("    float theta_i = acos(vectors.n_dot_l);")
        code.append("    float alpha = max(theta_r, theta_i);")
        code.append("    float beta = min(theta_r, theta_i);")
        code.append(
            "    float delta = "
            "dot(normalize(vectors.obs_dir - vectors.normal * vectors.n_dot_v),"
            " normalize(vectors.light_dir - vectors.normal * vectors.n_dot_l));"
        )
        code.append("    float a = 1.0 - 0.5 * material.roughness_squared / (material.roughness_squared + 0.33);")
        code.append("    float b = 0.45 * material.roughness_squared / (material.roughness_squared + 0.09);")
        code.append("    float c = sin(alpha) * tan(beta);")
        code.append("    float diffuse_coef = max(0.0, vectors.n_dot_l) * (a + b * max(0.0, delta) * c);")
        code.append("    contribution += light_color * diffuse_coef * material.diffuse_color;")
        code.append("}")
        code.append("  return contribution;")
        code.append("}")

    def fragment_extra(self, code):
        self.oren_nayar_material(code)
        self.oren_nayar_vectors(code)
        self.oren_nayar_calc_vectors(code)
        self.oren_nayar_brdf(code)

    def prepare_material(self, code):
        code.append("  OrenNayarMaterial material;")
        code.append("  material.diffuse_color = surface_color.rgb;")
        if self.appearance.has_specular:
            code.append("  material.specular_color = specular_color.rgb;")
            code.append("  material.shininess = shininess;")
        code.append("  material.roughness_squared = roughness_squared;")
        code.append("  vec3 obs_dir = normalize(-eye_vertex);")

    def light_contribution(self, code, result, light_direction, light_color):
        code.append(f"    OrenNayarVectors vectors = calc_oren_nayar_vectors(eye_normal, obs_dir, {light_direction});")
        code.append(f"    {result} = oren_nayar_brdf(material, vectors, {light_direction}, {light_color}.rgb);")

    def ambient_contribution(self, code, result, ambient_diffuse):
        code.append(f"    {result} = material.diffuse_color * {ambient_diffuse}.rgb;")

    def cos_light_normal(self):
        return "vectors.n_dot_l"
