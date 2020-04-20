#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2020 Laurent Deru.
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

from __future__ import print_function
from __future__ import absolute_import

from .shaders import LightingModel

from . import settings

class PbrLightingModel(LightingModel):
    use_vertex = True
    use_vertex_frag = True
    world_vertex = True
    use_normal = True
    use_normal = True
    world_normal = True

    def get_id(self):
        return "pbr"

    def fragment_uniforms(self, code):
        code.append("uniform float ambient_coef;")
        code.append("uniform float backlit;")
        code.append("uniform vec3 light_dir;")
        code.append("uniform vec4 ambient_color;")
        code.append("uniform vec4 light_color;")

    def point_material(self, code):
        code.append('''
struct PointMaterial
{
    vec3 diffuse_color;
    float perceptual_roughness;
    float alpha_roughness;
    float alpha_roughness_squared;

    vec3 reflectance0;
    vec3 reflectance90;
    vec3 specular_color;
};
''')

    def point_vectors(self, code):
        code.append('''
struct PointVectors
{
    float n_dot_l;
    float n_dot_v;
    float n_dot_h;
    float l_dot_h;
    float v_dot_h;
};
''')

    def calc_point_vectors(self, code):
        code.append('''
PointVectors calc_point_vectors(vec3 normal, vec3 obs_dir, vec3 light_dir)
{
    vec3 half_vec = normalize(light_dir + obs_dir);

    float n_dot_l = clamp(dot(normal, light_dir), 0.0, 1.0);
    float n_dot_v = clamp(dot(normal, obs_dir), 0.0, 1.0);
    float n_dot_h = clamp(dot(normal, half_vec), 0.0, 1.0);
    float l_dot_h = clamp(dot(light_dir, half_vec), 0.0, 1.0);
    float v_dot_h = clamp(dot(obs_dir, half_vec), 0.0, 1.0);

    return PointVectors(
        n_dot_l,
        n_dot_v,
        n_dot_h,
        l_dot_h,
        v_dot_h
    );
}
''')

    def lambert_diffuse(self, code):
        code.append('''
vec3 lambert_diffuse(PointMaterial material, PointVectors vectors)
{
    return material.diffuse_color / pi;
}
''')

    def fresnel_schlick(self, code):
        code.append('''
vec3 fresnel_schlick(PointMaterial material, PointVectors vectors)
{
    return material.reflectance0 + (material.reflectance90 - material.reflectance0) * pow(clamp(1.0 - vectors.v_dot_h, 0.0, 1.0), 5.0);
}
''')

    def smith_joint(self, code):
        code.append('''
float smith_joint(PointMaterial material, PointVectors vectors)
{
    float GGXV = vectors.n_dot_l * sqrt(vectors.n_dot_v * vectors.n_dot_v * (1.0 - material.alpha_roughness_squared) + material.alpha_roughness_squared);
    float GGXL = vectors.n_dot_v * sqrt(vectors.n_dot_l * vectors.n_dot_l * (1.0 - material.alpha_roughness_squared) + material.alpha_roughness_squared);

    float GGX = GGXV + GGXL;
    if (GGX > 0.0)
    {
        return 0.5 / GGX;
    }
    return 0.0;
}
''')

    def trowbridge_reitz(self, code):
        code.append('''
float trowbridge_reitz(PointMaterial material, PointVectors vectors)
{
    float f = (vectors.n_dot_h * material.alpha_roughness_squared - vectors.n_dot_h) * vectors.n_dot_h + 1.0;
    return material.alpha_roughness_squared / (pi * f * f);
}
''')

    def calc_shade(self, code):
        code.append('''
vec3 calc_shade(PointMaterial material, PointVectors vectors)
{
    if (vectors.n_dot_l > 0.0 || vectors.n_dot_v > 0.0)
    {
        vec3 F = fresnel_schlick(material, vectors);
        float V = smith_joint(material, vectors);
        float D = trowbridge_reitz(material, vectors);

        vec3 diffuse = (1.0 - F) * lambert_diffuse(material, vectors);
        vec3 specular = F * V * D;

        return vectors.n_dot_l * (diffuse + specular);
    } else {
        return vec3(0.0, 0.0, 0.0);
    }
}
''')

    def fragment_extra(self, code):
        self.shader.fragment_shader.add_function(code, 'point_material', self.point_material)
        self.shader.fragment_shader.add_function(code, 'point_vectors', self.point_vectors)
        self.shader.fragment_shader.add_function(code, 'calc_point_vectors', self.calc_point_vectors)
        self.shader.fragment_shader.add_function(code, 'lambert_diffuse', self.lambert_diffuse)
        self.shader.fragment_shader.add_function(code, 'fresnel_schlick', self.fresnel_schlick)
        self.shader.fragment_shader.add_function(code, 'smith_joint', self.smith_joint)
        self.shader.fragment_shader.add_function(code, 'trowbridge_reitz', self.trowbridge_reitz)
        self.shader.fragment_shader.add_function(code, 'calc_shade', self.calc_shade)
        code.append("vec3 f0 = vec3(0.04);")

    def fragment_shader(self, code):
        code.append("vec3 obs_dir = normalize(-world_vertex);")
        code.append("metallic = clamp(metallic, 0, 1);")
        code.append("perceptual_roughness = clamp(perceptual_roughness, 0, 1);")
        code.append("PointMaterial material;")
        code.append("material.diffuse_color = surface_color.rgb * (vec3(1.0) - f0) * (1.0 - metallic);")
        code.append("material.specular_color = mix(f0, surface_color.rgb, metallic);")
        code.append("material.perceptual_roughness = perceptual_roughness;")
        code.append("material.alpha_roughness = perceptual_roughness * perceptual_roughness;")
        code.append("material.alpha_roughness_squared = material.alpha_roughness * material.alpha_roughness;")
        code.append("float reflectance = max(max(material.specular_color.r, material.specular_color.g), material.specular_color.b);")
        code.append("material.reflectance0 = material.specular_color.rgb;")
        code.append("material.reflectance90 = vec3(clamp(reflectance * 50.0, 0.0, 1.0));")
        #TODO: Loop here over light sources
        code.append('PointVectors vectors = calc_point_vectors(normal, obs_dir, light_dir);')
        code.append("vec3 shade = calc_shade(material, vectors);")
        code.append("total_diffuse_color.rgb = vectors.n_dot_l * light_color.rgb * shade, 1.0 * shadow;")
        code.append("total_diffuse_color.a = surface_color.a;")

        code.append("if (vectors.n_dot_l < 0.0) {")
        if self.appearance.has_night:
            code.append("  float emission_coef = clamp(sqrt(-vectors.n_dot_l), 0.0, 1.0);")
            code.append("  total_emission_color.rgb = night_color.rgb * emission_coef;")
        code.append("  total_emission_color.rgb += material.diffuse_color * backlit * sqrt(-vectors.n_dot_l);")
        code.append("}")

    def update_shader_shape(self, shape, appearance):
        light_dir = shape.owner.vector_to_star
        light_color = shape.owner.light_color
        shape.instance.setShaderInput("light_dir", *light_dir)
        shape.instance.setShaderInput("light_color", light_color)
        shape.instance.setShaderInput("ambient_coef", settings.corrected_global_ambient)
        shape.instance.setShaderInput("ambient_color", (1, 1, 1, 1))
        shape.instance.setShaderInput("backlit", appearance.backlit)
