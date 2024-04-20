#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2023 Laurent Deru.
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


from ..component import ShaderComponent
from .base import ShaderShadowInterface
from ... import settings

class ShaderShadowMap(ShaderComponent, ShaderShadowInterface):

    fragment_requires = {'eye_vertex', 'eye_normal'}

    def __init__(self, name, use_bias):
        ShaderComponent.__init__(self)
        self.name = name
        self.use_bias = use_bias
        self.use_slope_scale_bias = settings.shadows_slope_scale_bias
        self.use_pcf_16 = settings.shader_version >= 130 and settings.shadows_pcf_16

    def get_id(self):
        name = 'sm-' + self.name
        if self.use_bias:
            name += '-b'
        if self.use_slope_scale_bias:
            name += '-sl'
        if self.use_pcf_16:
            name += '-pcf16'
        return name

    def vertex_uniforms(self, code):
        code.append("uniform mat4 trans_view_to_clip_of_%sLightSource;" % self.name)
        if self.use_bias:
            code.append("uniform float %s_shadow_normal_bias;" % self.name)
            code.append("uniform float %s_shadow_slope_bias;" % self.name)
            code.append("uniform float %s_shadow_depth_bias;" % self.name)

    def vertex_outputs(self, code):
        code.append("out vec4 %s_lightcoord;" % self.name)

    def get_bias(self, code):
        #http://the-witness.net/news/2013/09/shadow-mapping-summary-part-1/
        code.append('''
vec3 get_bias(float slope_bias, float normal_bias, vec3 normal, vec3 light_dir) {
    float cos_alpha = clamp(dot(normal, light_dir), 0.0, 1.0);
    float offset_scale_n = sqrt(1 - cos_alpha * cos_alpha);       // sin(acos(L.N))
    float offset_scale_l = min(2, offset_scale_n / cos_alpha);    // tan(acos(L.N))
    vec3 offset = normal * offset_scale_n * normal_bias + light_dir * offset_scale_l * slope_bias;
    return offset;
}
''')

    def vertex_extra(self, code):
        if self.use_bias:
            self.shader.fragment_shader.add_function(code, 'shadow_get_bias', self.get_bias)

    def prepare_shadow_for(self, code, light, light_direction, eye_light_direction):
        if self.use_bias:
            code.append(f"vec3 %s_offset = get_bias(%s_shadow_normal_bias, %s_shadow_slope_bias, eye_normal, {light_direction});" % (self.name, self.name, self.name))
            code.append("vec4 %s_lightclip = trans_view_to_clip_of_%sLightSource * (eye_vertex4 + vec4(%s_offset, 0.0));" % (self.name, self.name, self.name))
            code.append("%s_lightclip.z -= %s_shadow_depth_bias * %s_lightclip.w;" % (self.name, self.name, self.name))
        else:
            code.append("vec4 %s_lightclip = trans_view_to_clip_of_%sLightSource * eye_vertex4;" % (self.name, self.name))
        code.append("%s_lightcoord = %s_lightclip * vec4(0.5, 0.5, 0.5, 1.0) + %s_lightclip.w * vec4(0.5, 0.5, 0.5, 0.0);" % (self.name, self.name, self.name))

    def fragment_uniforms(self, code):
        code.append("uniform sampler2DShadow %s_depthmap;" % self.name)
        code.append("uniform float %s_shadow_coef;" % self.name)

    def fragment_inputs(self, code):
        code.append("in vec4 %s_lightcoord;" % self.name)

    def pcf_16(self, code):
        code.append('''
float shadow_pcf_16(sampler2DShadow shadow_map, vec4 shadow_coord)
{
    float shadow = 0.0;
    if (shadow_coord.w > .0)
    {
        vec2 pixel_size = 1.0 / textureSize(shadow_map, 0).xy;
        float x, y;
        for (y = -1.5 ; y <= 1.5 ; y += 1.0) {
            for (x = -1.5 ; x <= 1.5 ; x += 1.0) {
                float offset_x = x * pixel_size.x * shadow_coord.w;
                float offset_y = y * pixel_size.y * shadow_coord.w;
                shadow += textureProj(shadow_map, vec4(shadow_coord.x + offset_x, shadow_coord.y + offset_y, shadow_coord.z, shadow_coord.w));
            }
        }
        shadow /= 16.0;
    } else {
        shadow = 1.0;
    }
    return shadow;
}''')

    def fragment_extra(self, code):
        if self.use_pcf_16:
            self.shader.fragment_shader.add_function(code, 'shadow_pcf_16', self.pcf_16)

    def shadow_for(self, code, light, light_direction, eye_light_direction):
        if self.shader.fragment_shader.version < 130:
            code.append("local_shadow *= 1.0 - (1.0 - shadow2D(%s_depthmap, %s_lightcoord.xyz).x) * %s_shadow_coef;" % (self.name, self.name, self.name))
        else:
            if self.use_pcf_16:
                code.append("local_shadow *= 1.0 - (1.0 - shadow_pcf_16(%s_depthmap, %s_lightcoord)) * %s_shadow_coef;" % (self.name, self.name, self.name))
            else:
                code.append("local_shadow *= 1.0 - (1.0 - textureProj(%s_depthmap, %s_lightcoord)) * %s_shadow_coef;" % (self.name, self.name, self.name))
