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


class LambertPhongLightingModel(LightingModel):
    use_vertex = True
    world_vertex = True
    use_vertex_frag = True
    use_normal = True
    world_normal = True

    def get_id(self):
        return "lambert"

    def vertex_uniforms(self, code):
        LightingModel.vertex_uniforms(self, code)
        code.append("uniform vec3 light_dir;")

    def fragment_uniforms(self, code):
        LightingModel.fragment_uniforms(self, code)
        code.append("uniform float ambient_coef;")
        code.append("uniform float backlit;")
        code.append("uniform vec3 light_dir;")
        code.append("uniform vec4 ambient_color;")
        code.append("uniform vec4 light_color;")

    def fragment_shader(self, code):
        #TODO: should be done only using .rgb (or vec3) and apply alpha channel in the end
        code.append("vec4 total_diffuse = vec4(0.0);")
        code.append("float n_dot_l = dot(normal, light_dir);")
        code.append("if (n_dot_l > 0.0) {")
        if self.appearance.has_specular:
            code.append("  vec3 obs_dir = normalize(-world_vertex);")
            code.append("  vec3 half_vec = normalize(light_dir + obs_dir);")
            code.append("  float spec_angle = clamp(dot(normal, half_vec), 0.0, 1.0);")
            code.append("  vec4 specular = light_color * pow(spec_angle, shininess);")
            code.append("  total_diffuse_color.rgb += specular.rgb * specular_color.rgb * shadow;")
        code.append("  float diffuse_coef = clamp(n_dot_l, 0.0, 1.0) * shadow;")
        code.append("  total_diffuse += light_color * diffuse_coef;")
        code.append("}")
        #code.append("vec4 ambient = ambient_color * ambient_coef;")
        #if self.appearance.has_occlusion:
        #    code.append("ambient *= surface_occlusion;")
        #code.append("total_diffuse += ambient;")
        code.append("total_diffuse.a = 1.0;")
        code.append("total_diffuse_color += surface_color * total_diffuse;")
        self.apply_emission(code, 'n_dot_l')
