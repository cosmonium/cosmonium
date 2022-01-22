#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2022 Laurent Deru.
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


from .base import LightingModel


class OrenNayarPhongLightingModel(LightingModel):
    use_vertex = True
    world_vertex = True
    use_vertex_frag = True
    use_normal = True
    world_normal = True

    def get_id(self):
        return "oren-nayar"

    def vertex_uniforms(self, code):
        LightingModel.vertex_uniforms(self, code)
        code.append("uniform vec3 light_dir;")

    def fragment_uniforms(self, code):
        LightingModel.fragment_uniforms(self, code)
        code.append("uniform float ambient_coef;")
        code.append("uniform vec3 light_dir;")
        code.append("uniform vec4 ambient_color;")
        code.append("uniform vec4 light_color;")
        code.append("uniform float backlit;")
        code.append("uniform float roughness_squared;")

    def fragment_shader(self, code):
        code.append("vec4 total_diffuse = vec4(0.0);")
        code.append("float l_dot_n = dot(light_dir, normal);")
        code.append("if (l_dot_n > 0.0) {")
        code.append("  vec3 obs_dir = normalize(-world_vertex);")
        if self.appearance.has_specular:
            code.append("  vec3 half_vec = normalize(light_dir + obs_dir);")
            code.append("  float spec_angle = clamp(dot(normal, half_vec), 0.0, 1.0);")
            code.append("  vec4 specular = light_color * pow(spec_angle, shininess);")
            code.append("  total_diffuse_color.rgb += specular.rgb * specular_factor.rgb * specular_color.rgb * shadow;")
        code.append("  float v_dot_n = dot(obs_dir, normal);")
        code.append("  float theta_r = acos(v_dot_n);")
        code.append("  float theta_i = acos(l_dot_n);")
        code.append("  float alpha = max(theta_r, theta_i);")
        code.append("  float beta = min(theta_r, theta_i);")
        code.append("  float delta = dot(normalize(obs_dir - normal * v_dot_n), normalize(light_dir - normal * l_dot_n));")
        code.append("  float a = 1.0 - 0.5 * roughness_squared / (roughness_squared + 0.33);")
        code.append("  float b = 0.45 * roughness_squared / (roughness_squared + 0.09);")
        code.append("  float c = sin(alpha) * tan(beta);")
        code.append("  float diffuse_coef = max(0.0, l_dot_n) * (a + b * max(0.0, delta) * c);")
        code.append("  vec4 diffuse = light_color * shadow * diffuse_coef;")
        code.append("  total_diffuse += diffuse;")
        code.append("}")
        #code.append("vec4 ambient = ambient_color * ambient_coef;")
        #code.append("total_diffuse += ambient;")
        code.append("total_diffuse.a = 1.0;")
        code.append("total_diffuse_color += surface_color * total_diffuse;")
        self.apply_emission(code, 'l_dot_n')
