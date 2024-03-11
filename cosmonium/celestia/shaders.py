#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2024 Laurent Deru.
#
#Cosmonium is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Cosmonium is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#


from ..shaders.component import ShaderComponent
from ..shaders.lighting.lambert import BRDFInterface


class LunarLambertLightingModel(ShaderComponent, BRDFInterface):

    fragment_requires = {'eye_vertex', 'eye_normal'}

    def get_id(self):
        return "lunar"

    def lunar_lambert_material(self, code):
        code.append("struct LunarLambertMaterial")
        code.append("{")
        code.append("    vec3 diffuse_color;")
        code.append("};")

    def lunar_lambert_vectors(self, code):
        code.append("struct LunarLambertVectors")
        code.append("{")
        code.append("    float n_dot_l;")
        code.append("    float n_dot_v;")
        code.append("};")

    def lunar_lambert_calc_vectors(self, code):
        code.append("LunarLambertVectors calc_lunar_lambert_vectors(vec3 normal, vec3 obs_dir, vec3 light_dir)")
        code.append("{")
        code.append("    float n_dot_l = min(dot(normal, light_dir), 1.0);")
        code.append("    float n_dot_v = min(dot(normal, obs_dir), 1.0);")
        code.append("    return LunarLambertVectors(")
        code.append("        n_dot_l,")
        code.append("        n_dot_v")
        code.append("    );")
        code.append("}")

    def lunar_lambert_brdf(self, code):
        code.append(
            "vec3 lunar_lambert_brdf("
            "in LunarLambertMaterial material, in LunarLambertVectors vectors, "
            "in vec3 light_direction, in vec3 light_color) {")
        code.append("  vec3 contribution = vec3(0);")
        code.append("  if (vectors.n_dot_l > 0.0) {")
        code.append(
            "  float diffuse_coef = "
            "clamp(vectors.n_dot_l / (max(vectors.n_dot_v, 0.001) + vectors.n_dot_l), 0.0, 1.0);")
        code.append("    contribution += light_color * diffuse_coef * material.diffuse_color;")
        code.append("  }")
        code.append("  return contribution;")
        code.append("}")

    def fragment_extra(self, code):
        self.lunar_lambert_material(code)
        self.lunar_lambert_vectors(code)
        self.lunar_lambert_calc_vectors(code)
        self.lunar_lambert_brdf(code)

    def prepare_material(self, code):
        code.append("  LunarLambertMaterial material;")
        code.append("  material.diffuse_color = surface_color.rgb;")
        code.append("  vec3 obs_dir = normalize(-eye_vertex);")

    def light_contribution(self, code, result, light_direction, light_color):
        code.append(
            "    LunarLambertVectors vectors = "
            f"calc_lunar_lambert_vectors(eye_normal, obs_dir, {light_direction});")
        code.append(f"    {result} = lunar_lambert_brdf(material, vectors, {light_direction}, {light_color}.rgb);")

    def ambient_contribution(self, code, result, ambient_diffuse):
        code.append(f"    {result} = material.diffuse_color * {ambient_diffuse}.rgb;")

    def cos_light_normal(self):
        return "vectors.n_dot_l"
