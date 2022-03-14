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


from .base import ShaderDataSource
from ... import settings


class HeightmapShaderDataSource(ShaderDataSource):
    def __init__(self, heightmap, data_store, normals=True):
        ShaderDataSource.__init__(self)
        self.heightmap = heightmap
        self.name = self.heightmap.name
        self.has_normal = normals
        self.interpolator = heightmap.interpolator.get_data_source_interpolator()
        self.filtering = heightmap.filter.get_data_source_filtering()
        self.data_store = data_store

    def get_id(self):
        str_id = self.name + self.interpolator.get_id() + self.filtering.get_id()
        return str_id

    def vertex_uniforms(self, code):
        code.append("uniform sampler2D heightmap_%s;" % self.name)
        if not self.data_store:
            code.append("uniform float heightmap_%s_height_scale;" % self.name)
            code.append("uniform float heightmap_%s_u_scale;" % self.name)
            code.append("uniform float heightmap_%s_v_scale;" % self.name)
            code.append("uniform vec2 heightmap_%s_offset;" % self.name)
            code.append("uniform vec2 heightmap_%s_scale;" % self.name)

    def fragment_uniforms(self, code):
        code.append("uniform sampler2D heightmap_%s;" % self.name)
        if not self.data_store:
            code.append("uniform float heightmap_%s_height_scale;" % self.name)
            code.append("uniform float heightmap_%s_u_scale;" % self.name)
            code.append("uniform float heightmap_%s_v_scale;" % self.name)
            code.append("uniform vec2 heightmap_%s_offset;" % self.name)
            code.append("uniform vec2 heightmap_%s_scale;" % self.name)

    def decode_height(self, code):
        if settings.encode_float:
            code += ['''
float decode_height(vec4 encoded) {
    return DecodeFloatRGBA(encoded);
}
''']
        else:
            code += ['''
float decode_height(vec4 encoded) {
    return encoded.x;
}
''']
    def get_terrain_height(self, code):
        code += ['''
float get_terrain_height_%s(sampler2D heightmap, vec2 texcoord, HeightmapParameters params) {
    vec2 pos = texcoord * params.scale + params.offset;
    return decode_height(%s) * params.height_scale + %g;
}
''' % (self.name, self.filtering.apply('heightmap', 'pos'), self.heightmap.height_offset)]

    def get_terrain_normal(self, code):
        code += ['''
vec3 get_terrain_normal_%s(sampler2D heightmap, vec2 texcoord, HeightmapParameters params) {
    vec3 pixel_size = vec3(1.0, -1.0, 0) / textureSize(heightmap, 0).xxx;
    float u0 = get_terrain_height_%s(heightmap, texcoord + pixel_size.yz, params);
    float u1 = get_terrain_height_%s(heightmap, texcoord + pixel_size.xz, params);
    float v0 = get_terrain_height_%s(heightmap, texcoord + pixel_size.zy, params);
    float v1 = get_terrain_height_%s(heightmap, texcoord + pixel_size.zx, params);
    float deltax = u1 - u0;
    float deltay = v1 - v0;
    //float deltax = textureBSplineDerivX(heightmap, texcoord);
    //float deltay = textureBSplineDerivY(heightmap, texcoord);
    vec3 tangent = normalize(vec3(2.0 * params.u_scale, 0, deltax));
    vec3 binormal = normalize(vec3(0, 2.0 * params.v_scale, deltay));
    return normalize(cross(tangent, binormal));
}
''' % (self.name, self.name, self.name, self.name, self.name)]

    def has_source_for(self, source):
        if source == 'height':
            return True
        elif source == 'normal':
            return self.has_normal
        else:
            return False

    def get_source_for(self, source, param, error=True):
        if source == 'height_%s' % self.name:
            return "get_terrain_height_%s(heightmap_%s, %s, heightmap_%s_params)" % (self.name, self.name, param, self.name)
        if source == 'normal_%s' % self.name or (self.has_normal and source == 'normal'):
            return "get_terrain_normal_%s(heightmap_%s, %s, heightmap_%s_params)" \
                    % (self.name, self.name, "texcoord0.xy", self.name)
        if source == 'range_%s' % self.name:
            return str(1.0 / (self.heightmap.max_height - self.heightmap.min_height))
        if error: print("Unknown source '%s' requested" % source)
        return ''

    def heightmap_struct(self, code):
        code.append("""
struct HeightmapParameters {
    float height_scale;
    float u_scale;
    float v_scale;
    vec2 offset;
    vec2 scale;
};
""")

    def vertex_extra(self, code):
        if settings.encode_float:
            self.shader.vertex_shader.add_decode_rgba(code)
        self.shader.vertex_shader.add_function(code, 'heightmap_struct', self.heightmap_struct)
        self.shader.vertex_shader.add_function(code, 'decode_height', self.decode_height)
        self.interpolator.extra(self.shader.vertex_shader, code)
        self.filtering.extra(self.shader.vertex_shader, code)
        self.shader.vertex_shader.add_function(code, 'get_terrain_height_%s' % self.name, self.get_terrain_height)

    def fragment_extra(self, code):
        if settings.encode_float:
            self.shader.fragment_shader.add_decode_rgba(code)
        self.shader.fragment_shader.add_function(code, 'heightmap_struct', self.heightmap_struct)
        self.shader.fragment_shader.add_function(code, 'decode_height', self.decode_height)
        self.interpolator.extra(self.shader.fragment_shader, code)
        self.filtering.extra(self.shader.fragment_shader, code)
        self.shader.fragment_shader.add_function(code, 'get_terrain_height_%s' % self.name, self.get_terrain_height)
        self.shader.fragment_shader.add_function(code, 'get_terrain_normal_%s' % self.name, self.get_terrain_normal)

    def vertex_shader_decl(self, code):
        code.append("HeightmapParameters heightmap_%s_params;" % self.name)
        if self.data_store:
            code.append("vec4 encoded_data_%s;" % self.name)
            code.append("encoded_data_%s = texelFetch(data_store, entry_id * 2, 0);" % self.name)
            code.append("heightmap_%s_params.height_scale = encoded_data_%s.x;" % (self.name, self.name))
            code.append("heightmap_%s_params.u_scale = encoded_data_%s.y;" % (self.name, self.name))
            code.append("heightmap_%s_params.v_scale = encoded_data_%s.z;" % (self.name, self.name))
            code.append("encoded_data_%s = texelFetch(data_store, entry_id * 2 + 1, 0);" % self.name)
            code.append("heightmap_%s_params.offset = encoded_data_%s.xy;" % (self.name, self.name))
            code.append("heightmap_%s_params.scale = encoded_data_%s.zw;" % (self.name, self.name))
        else:
            code.append("heightmap_%s_params.height_scale = heightmap_%s_height_scale;" % (self.name, self.name))
            code.append("heightmap_%s_params.u_scale = heightmap_%s_u_scale;" % (self.name, self.name))
            code.append("heightmap_%s_params.v_scale = heightmap_%s_v_scale;" % (self.name, self.name))
            code.append("heightmap_%s_params.offset = heightmap_%s_offset;" % (self.name, self.name))
            code.append("heightmap_%s_params.scale = heightmap_%s_scale;" % (self.name, self.name))

    def fragment_shader_decl(self, code):
        code.append("HeightmapParameters heightmap_%s_params;" % self.name)
        if self.data_store:
            code.append("vec4 encoded_data_%s;" % self.name)
            code.append("encoded_data_%s = texelFetch(data_store, entry_id * 2, 0);" % self.name)
            code.append("heightmap_%s_params.height_scale = encoded_data_%s.x;" % (self.name, self.name))
            code.append("heightmap_%s_params.u_scale = encoded_data_%s.y;" % (self.name, self.name))
            code.append("heightmap_%s_params.v_scale = encoded_data_%s.z;" % (self.name, self.name))
            code.append("encoded_data_%s = texelFetch(data_store, entry_id * 2 + 1, 0);" % self.name)
            code.append("heightmap_%s_params.offset = encoded_data_%s.xy;" % (self.name, self.name))
            code.append("heightmap_%s_params.scale = encoded_data_%s.zw;" % (self.name, self.name))
        else:
            code.append("heightmap_%s_params.height_scale = heightmap_%s_height_scale;" % (self.name, self.name))
            code.append("heightmap_%s_params.u_scale = heightmap_%s_u_scale;" % (self.name, self.name))
            code.append("heightmap_%s_params.v_scale = heightmap_%s_v_scale;" % (self.name, self.name))
            code.append("heightmap_%s_params.offset = heightmap_%s_offset;" % (self.name, self.name))
            code.append("heightmap_%s_params.scale = heightmap_%s_scale;" % (self.name, self.name))
