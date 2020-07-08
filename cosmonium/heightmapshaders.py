#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2019 Laurent Deru.
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

from .shaders import DataSource, VertexControl
from .textures import DataTexture
from . import settings

class DisplacementVertexControl(VertexControl):
    use_normal = True

    def __init__(self, heightmap, create_normals=False, shader=None):
        VertexControl.__init__(self, shader)
        self.heightmap = heightmap
        self.has_normal = create_normals
        if create_normals:
            self.use_tangent = True

    def get_id(self):
        return "dis-" + self.heightmap.name

    def vertex_outputs(self, code):
        code.append('out float vertex_height;')

    def fragment_inputs(self, code):
        code.append("in float vertex_height;")

    def update_vertex(self, code):
        code.append("vertex_height = %s;" % self.shader.data_source.get_source_for('height_%s' % self.heightmap.name, 'model_texcoord0.xy'))
        code.append("model_vertex4 = model_vertex4 + model_normal4 * vertex_height;")

    def update_normal(self, code):
        code.append("vec3 normal = model_normal4.xyz;")
        code.append('vec3 surface_normal = %s;' % self.shader.data_source.get_source_for('normal_%s' % self.heightmap.name, 'model_texcoord0.xy'))
        code.append("normal *= surface_normal.z;")
        code.append("normal += model_tangent4.xyz * surface_normal.x;")
        code.append("normal += model_tangent4.xyz * surface_normal.y;")
        code.append("normal = normalize(normal);")
        code.append("model_normal4 = vec4(normal, 0.0);")

class HeightmapDataSource(DataSource):
    F_none = 0
    F_improved_bilinear = 1
    F_quintic = 2
    F_bspline = 3

    def __init__(self, heightmap, normals=True, shader=None):
        DataSource.__init__(self, shader)
        self.heightmap = heightmap
        self.name = self.heightmap.name
        self.has_normal = normals
        self.filtering = heightmap.interpolator.get_data_source_filtering()

    def get_id(self):
        str_id = self.name
        config = ''
        if self.filtering == self.F_improved_bilinear:
            config = 'i'
        elif self.filtering == self.F_quintic:
            config = 'q'
        elif self.filtering == self.F_bspline:
            config = 'b'
        if config != '':
            str_id += '-' + config
        return str_id

    def vertex_uniforms(self, code):
        code.append("uniform sampler2D heightmap_%s;" % self.name)
        code.append("uniform float heightmap_%s_height_scale;" % self.name)
        code.append("uniform float heightmap_%s_u_scale;" % self.name)
        code.append("uniform float heightmap_%s_v_scale;" % self.name)
        code.append("uniform vec2 heightmap_%s_offset;" % self.name)
        code.append("uniform vec2 heightmap_%s_scale;" % self.name)

    def fragment_uniforms(self, code):
        code.append("uniform sampler2D heightmap_%s;" % self.name)
        code.append("uniform float heightmap_%s_height_scale;" % self.name)
        code.append("uniform float heightmap_%s_u_scale;" % self.name)
        code.append("uniform float heightmap_%s_v_scale;" % self.name)
        code.append("uniform vec2 heightmap_%s_offset;" % self.name)
        code.append("uniform vec2 heightmap_%s_scale;" % self.name)

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
    def textureInter(self, code):
        code += ['''
vec4 textureInter( sampler2D sam, vec2 p )
{
    vec2 res = textureSize( sam, 0 );
    p = p*res + 0.5;

    vec2 i = floor(p);
    vec2 f = p - i;
    f = f*f*f*(f*(f*6.0-15.0)+10.0);
    p = i + f;

    p = (p - 0.5)/res;
    return texture2D( sam, p );
}
''']

    def textureBSpline(self, code):
        code += ['''
vec4 cubic(float alpha) {
    float alpha2 = alpha*alpha;
    float alpha3 = alpha2*alpha;
    float w0 = 1./6. * (-alpha3 + 3.*alpha2 - 3.*alpha + 1.);
    float w1 = 1./6. * (3.*alpha3 - 6.*alpha2 + 4.);
    float w2 = 1./6. * (-3.*alpha3 + 3.*alpha2 + 3.*alpha + 1.);
    float w3 = 1./6. * alpha3;
    return vec4(w0, w1, w2, w3);
}

vec4 textureBSpline(sampler2D sam, vec2 pos)
{
    vec2 texSize = textureSize(sam, 0);
    pos *= texSize;
    vec2 tc = floor(pos - 0.5) + 0.5;

    vec2 alpha = pos - tc;
    vec4 cubicx = cubic(alpha.x);
    vec4 cubicy = cubic(alpha.y);

    vec4 c = tc.xxyy + vec2 (-1., +1.).xyxy;
    
    vec4 s = vec4(cubicx.xz + cubicx.yw, cubicy.xz + cubicy.yw);
    vec4 offset = c + vec4 (cubicx.yw, cubicy.yw) / s;

    offset /= texSize.xxyy;

    float sx = s.x / (s.x + s.y);
    float sy = s.z / (s.z + s.w);

    float p00 = texture2D(sam, offset.xz).x;
    float p01 = texture2D(sam, offset.yz).x;
    float p10 = texture2D(sam, offset.xw).x;
    float p11 = texture2D(sam, offset.yw).x;

    float a = mix(p01, p00, sx);
    float b = mix(p11, p10, sx);
    return vec4(mix(b, a, sy));
}''']

    def textureBSplineDelta(self, code):
        code += ['''
vec4 cubic_deriv(float alpha) {
    float alpha2 = alpha * alpha;
    float w0 = -0.5 * alpha2 + alpha -0.5;
    float w1 = 1.5 * alpha2 - 2.0 * alpha;
    float w2 = -1.5 * alpha2 + alpha + 0.5;
    float w3 = 0.5 * alpha2;
    return vec4(w0, w1, w2, w3);
}

float textureBSplineDerivX(sampler2D sam, vec2 pos)
{
    vec2 texSize = textureSize(sam, 0);
    pos *= texSize;
    vec2 tc = floor(pos - 0.5) + 0.5;

    vec2 alpha = pos - tc;
    vec4 cubicx = cubic_deriv(alpha.x);
    vec4 cubicy = cubic(alpha.y);

    vec4 c = tc.xxyy + vec2 (-1., +1.).xyxy;
    
    vec4 s = vec4(cubicx.xz + cubicx.yw, cubicy.xz + cubicy.yw);
    vec4 offset = c + vec4 (cubicx.yw, cubicy.yw) / s;

    offset /= texSize.xxyy;

    float sx = s.x / (s.x + s.y);
    float sy = s.z / (s.z + s.w);

    float p00 = texture2D(sam, offset.xz).x;
    float p01 = texture2D(sam, offset.yz).x;
    float p10 = texture2D(sam, offset.xw).x;
    float p11 = texture2D(sam, offset.yw).x;

    float a = mix(p01, p00, sx);
    float b = mix(p11, p10, sx);
    return (b - a) * sy;
}
float textureBSplineDerivY(sampler2D sam, vec2 pos)
{
    vec2 texSize = textureSize(sam, 0);
    pos *= texSize;
    vec2 tc = floor(pos - 0.5) + 0.5;

    vec2 alpha = pos - tc;
    vec4 cubicx = cubic(alpha.x);
    vec4 cubicy = cubic_deriv(alpha.y);

    vec4 c = tc.xxyy + vec2 (-1., +1.).xyxy;
    
    vec4 s = vec4(cubicx.xz + cubicx.yw, cubicy.xz + cubicy.yw);
    vec4 offset = c + vec4 (cubicx.yw, cubicy.yw) / s;

    offset /= texSize.xxyy;

    float sx = s.x / (s.x + s.y);
    float sy = s.z / (s.z + s.w);

    float p00 = texture2D(sam, offset.xz).x;
    float p01 = texture2D(sam, offset.yz).x;
    float p10 = texture2D(sam, offset.xw).x;
    float p11 = texture2D(sam, offset.yw).x;

    float a = (p01 - p00) * sx;
    float b = (p11 - p10) * sx;
    return mix(b, a, sy);
}
''']

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
        if self.filtering == self.F_improved_bilinear:
            sampler = 'textureGood'
        elif self.filtering == self.F_quintic:
            sampler = 'textureInter'
        elif self.filtering == self.F_bspline:
            sampler = 'textureBSpline'
        else:
            sampler = 'texture2D'
        code += ['''
float get_terrain_height_%s(sampler2D heightmap, vec2 texcoord, float height_scale, vec2 offset, vec2 scale) {
    vec2 pos = texcoord * scale + offset;
    return decode_height(%s(heightmap, pos)) * height_scale;// + %g;
}
''' % (self.name, sampler, self.heightmap.offset)]

    def get_terrain_normal(self, code):
        code += ['''
vec3 get_terrain_normal_%s(sampler2D heightmap, vec2 texcoord, float height_scale, vec2 offset, vec2 scale, float u_scale, float v_scale) {
    vec3 pixel_size = vec3(1.0, -1.0, 0) / textureSize(heightmap, 0).xxx;
    float u0 = get_terrain_height_%s(heightmap, texcoord + pixel_size.yz, height_scale, offset, scale);
    float u1 = get_terrain_height_%s(heightmap, texcoord + pixel_size.xz, height_scale, offset, scale);
    float v0 = get_terrain_height_%s(heightmap, texcoord + pixel_size.zy, height_scale, offset, scale);
    float v1 = get_terrain_height_%s(heightmap, texcoord + pixel_size.zx, height_scale, offset, scale);
    float deltax = u1 - u0;
    float deltay = v1 - v0;
    //float deltax = textureBSplineDerivX(heightmap, texcoord);
    //float deltay = textureBSplineDerivY(heightmap, texcoord);
    vec3 tangent = normalize(vec3(2.0 * u_scale, 0, deltax));
    vec3 binormal = normalize(vec3(0, 2.0 * v_scale, -deltay));
    return normalize(cross(tangent, binormal));
}
''' % (self.name, self.name, self.name, self.name, self.name)]

    def has_source_for(self, source):
        return self.has_normal and source == 'normal'

    def get_source_for(self, source, param, error=True):
        if source == 'height_%s' % self.name:
            return "get_terrain_height_%s(heightmap_%s, %s, heightmap_%s_height_scale, heightmap_%s_offset, heightmap_%s_scale)" % (self.name, self.name, param, self.name, self.name, self.name)
        if source == 'normal_%s' % self.name or (self.has_normal and source == 'normal'):
            return "get_terrain_normal_%s(heightmap_%s, %s, heightmap_%s_height_scale, heightmap_%s_offset, heightmap_%s_scale, heightmap_%s_u_scale, heightmap_%s_v_scale)" \
                    % (self.name, self.name, "texcoord0.xy", self.name, self.name, self.name, self.name, self.name)
        if error: print("Unknown source '%s' requested" % source)
        return ''

    def vertex_extra(self, code):
        if settings.encode_float:
            self.shader.vertex_shader.add_decode_rgba(code)
        self.shader.vertex_shader.add_function(code, 'decode_height', self.decode_height)
        if self.filtering == self.F_improved_bilinear:
            self.shader.vertex_shader.add_function(code, 'textureGood', self.textureGood)
        elif self.filtering == self.F_quintic:
            self.shader.vertex_shader.add_function(code, 'textureInter', self.textureInter)
        elif self.filtering == self.F_bspline:
            self.shader.vertex_shader.add_function(code, 'textureBSpline', self.textureBSpline)
        self.shader.vertex_shader.add_function(code, 'get_terrain_height_%s' % self.name, self.get_terrain_height)

    def fragment_extra(self, code):
        if settings.encode_float:
            self.shader.fragment_shader.add_decode_rgba(code)
        self.shader.fragment_shader.add_function(code, 'decode_height', self.decode_height)
        if self.filtering == self.F_improved_bilinear:
            self.shader.fragment_shader.add_function(code, 'textureGood', self.textureGood)
        elif self.filtering == self.F_quintic:
            self.shader.fragment_shader.add_function(code, 'textureInter', self.textureInter)
        elif self.filtering == self.F_bspline:
            self.shader.fragment_shader.add_function(code, 'textureBSpline', self.textureBSpline)
            self.shader.fragment_shader.add_function(code, 'textureBSplineDelta', self.textureBSplineDelta)
        self.shader.fragment_shader.add_function(code, 'get_terrain_height_%s' % self.name, self.get_terrain_height)
        self.shader.fragment_shader.add_function(code, 'get_terrain_normal_%s' % self.name, self.get_terrain_normal)

    def update_shader_patch_static(self, shape, patch, appearance):
        heightmap = self.heightmap.get_heightmap(patch)
        patch.instance.set_shader_input('heightmap_%s' % self.name, heightmap.texture)
        #TODO: replace this by a vec3
        patch.instance.set_shader_input("heightmap_%s_height_scale" % self.name, self.heightmap.get_height_scale(patch))
        patch.instance.set_shader_input("heightmap_%s_u_scale" % self.name, self.heightmap.get_u_scale(patch))
        patch.instance.set_shader_input("heightmap_%s_v_scale" % self.name, self.heightmap.get_v_scale(patch))
        patch.instance.set_shader_input("heightmap_%s_offset" % self.name, self.heightmap.get_texture_offset(patch))
        patch.instance.set_shader_input("heightmap_%s_scale" % self.name, self.heightmap.get_texture_scale(patch))

class StackedHeightmapDataSource(DataSource):
    def __init__(self, heightmap, texture_class, shader=None):
        DataSource.__init__(self, shader)
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

    def update_shader_patch_static(self, shape, patch, appearance):
        #TODO: Berk, should be either done in texture load or now switch to explicit heightmap generation in patchedshape
        heightmap = self.heightmap.get_or_create_heightmap(patch)
        for i, texture_source in enumerate(self.texture_sources):
            texture_source.load(patch)
            texture_source.apply(patch, 'heightmap_%s' % self.heightmap.heightmaps[i].name)
            patch.instance.set_shader_input("heightmap_%s_height_scale" % self.heightmap.heightmaps[i].name, self.heightmap.heightmaps[i].get_height_scale(patch))
        patch.instance.set_shader_input("heightmap_%s_u_scale" % self.name, self.heightmap.get_u_scale(patch))
        patch.instance.set_shader_input("heightmap_%s_v_scale" % self.name, self.heightmap.get_v_scale(patch))
