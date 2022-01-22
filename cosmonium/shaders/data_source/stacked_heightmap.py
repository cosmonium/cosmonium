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
from ...textures import DataTexture
from ... import settings


class StackedHeightmapDataSource(ShaderDataSource):
    def __init__(self, heightmap, texture_class, shader=None):
        ShaderDataSource.__init__(self, shader)
        self.heightmap = heightmap
        self.texture_sources = []
        for heightmap in self.heightmap.heightmaps:
            self.texture_sources.append(DataTexture(texture_class(heightmap)))
        self.name = self.heightmap.name
        self.has_normal_texture = True

    def vertex_uniforms(self, code):
        for heightmap in self.heightmap.heightmaps:
            code.append("uniform sampler2D heightmap_%s;" % heightmap.name)
            code.append("uniform float heightmap_%s_height_scale;" % heightmap.name)
        code.append("uniform float heightmap_%s_u_scale;" % self.name)
        code.append("uniform float heightmap_%s_v_scale;" % self.name)

    def fragment_uniforms(self, code):
        for heightmap in self.heightmap.heightmaps:
            code.append("uniform sampler2D heightmap_%s;" % heightmap.name)
            code.append("uniform float heightmap_%s_height_scale;" % heightmap.name)
        code.append("uniform float heightmap_%s_u_scale;" % self.name)
        code.append("uniform float heightmap_%s_v_scale;" % self.name)

    def get_source_for(self, source, param, error=True):
        if source == 'height_%s' % self.name:
            return "get_terrain_height_%s(%s)" % (self.name, param)
        if source == 'normal_%s' % self.name:
            return "get_terrain_normal_%s(%s)" % (self.name, param)
        if error: print("Unknown source '%s' requested" % source)
        return ''

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
    return encoded[0];
}
''']

    def textureGood(self, code):
        code += ['''
vec4 textureGood( sampler2D sam, vec2 uv )
{
    vec2 res = textureSize( sam, 0 );

    vec2 st = uv*res - 0.5;

    vec2 iuv = floor( st );
    vec2 fuv = fract( st );

    vec4 a = texture2D( sam, (iuv+vec2(0.5,0.5))/res );
    vec4 b = texture2D( sam, (iuv+vec2(1.5,0.5))/res );
    vec4 c = texture2D( sam, (iuv+vec2(0.5,1.5))/res );
    vec4 d = texture2D( sam, (iuv+vec2(1.5,1.5))/res );

    return mix( mix( a, b, fuv.x),
                mix( c, d, fuv.x), fuv.y );
}
''']

    def get_terrain_height_named(self, code):
        code.append('float get_terrain_height_%s(vec2 texcoord) {' % self.name)
        code.append('float height = 0.0;')
        for heightmap in self.heightmap.heightmaps:
            code.append("height += decode_height(texture2D(heightmap_%s, texcoord)) * heightmap_%s_height_scale;" % (heightmap.name, heightmap.name))
        code.append('return height;')
        code.append('}')

    def get_terrain_normal_named(self, code):
        code.append('vec3 get_terrain_normal_%s(vec2 texcoord) {' % self.name)
        #TODO: Should fetch textureSize properly
        code.append('vec3 pixel_size = vec3(1.0, -1.0, 0) / textureSize(heightmap_%s, 0).xxx;' % self.heightmap.heightmaps[0].name)
        code.append('float u0 = get_terrain_height_%s(texcoord + pixel_size.yz);' % self.name)
        code.append('float u1 = get_terrain_height_%s(texcoord + pixel_size.xz);' % self.name)
        code.append('float v0 = get_terrain_height_%s(texcoord + pixel_size.zy);' % self.name)
        code.append('float v1 = get_terrain_height_%s(texcoord + pixel_size.zx);' % self.name)
        code.append('vec3 tangent = normalize(vec3(2.0 * heightmap_%s_u_scale, 0, u1 - u0));' % self.name)
        code.append('vec3 binormal = normalize(vec3(0, 2.0 * heightmap_%s_v_scale, v1 - v0));' % self.name)
        code.append('return normalize(cross(tangent, binormal));')
        code.append('}')

    def vertex_extra(self, code):
        if settings.encode_float:
            self.shader.vertex_shader.add_decode_rgba(code)
        self.textureGood(code)
        self.decode_height(code)
        self.get_terrain_height_named(code)

    def fragment_extra(self, code):
        if settings.encode_float:
            self.shader.fragment_shader.add_decode_rgba(code)
        self.textureGood(code)
        self.decode_height(code)
        self.get_terrain_height_named(code)
        self.get_terrain_normal_named(code)
