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


class TextureTilingSampler:
    sampler_2d_name = None
    sampler_2d_array_name = None

    def set_shader(self, shader):
        self.shader = shader

    def get_id(self):
        raise NotImplementedError()

    def sample(self, sampler, coord):
        return f"{self.sampler_2d_name}({sampler}, {coord})"

    def sample_array(self, sampler, coord, page):
        return f"{self.sampler_2d_array_name}({sampler}, vec3({coord}, {page}))"

    def uniforms(self, code):
        pass

    def extra(self, shader, code):
        pass


class DefaultSampler(TextureTilingSampler):
    sampler_2d_name = 'texture'
    sampler_2d_array_name = 'texture'

    def get_id(self):
        return ''

    def extra(self, shader, code):
        pass


class HashTextureTilingSampler(TextureTilingSampler):
    sampler_2d_name = 'textureNoTile2D'
    sampler_2d_array_name = 'textureNoTile2DArray'

    def get_id(self):
        return 'hash'

    def hash4(self, code):
        code.append('''
vec4 hash4( vec2 p ) { return fract(sin(vec4( 1.0+dot(p,vec2(37.0,17.0)),
                                              2.0+dot(p,vec2(11.0,47.0)),
                                              3.0+dot(p,vec2(41.0,29.0)),
                                              4.0+dot(p,vec2(23.0,31.0))))*103.0); }
''')

    def textureNoTile2D(self, code):
        code.append(
'''vec4 textureNoTile2D(sampler2D samp, in vec2 uv)
{
    vec2 iuv = floor(uv.xy);
    vec2 fuv = fract(uv.xy);

    // generate per-tile transform
    vec4 ofa = hash4(iuv + vec2(0.0, 0.0));
    vec4 ofb = hash4(iuv + vec2(1.0, 0.0));
    vec4 ofc = hash4(iuv + vec2(0.0, 1.0));
    vec4 ofd = hash4(iuv + vec2(1.0, 1.0));

    vec2 ddx = dFdx(uv.xy);
    vec2 ddy = dFdy(uv.xy);

    // transform per-tile uvs
    ofa.zw = sign(ofa.zw - 0.5);
    ofb.zw = sign(ofb.zw - 0.5);
    ofc.zw = sign(ofc.zw - 0.5);
    ofd.zw = sign(ofd.zw - 0.5);

    // uv's, and derivarives (for correct mipmapping)
    vec2 uva = uv.xy*ofa.zw + ofa.xy; vec2 ddxa = ddx*ofa.zw; vec2 ddya = ddy*ofa.zw;
    vec2 uvb = uv.xy*ofb.zw + ofb.xy; vec2 ddxb = ddx*ofb.zw; vec2 ddyb = ddy*ofb.zw;
    vec2 uvc = uv.xy*ofc.zw + ofc.xy; vec2 ddxc = ddx*ofc.zw; vec2 ddyc = ddy*ofc.zw;
    vec2 uvd = uv.xy*ofd.zw + ofd.xy; vec2 ddxd = ddx*ofd.zw; vec2 ddyd = ddy*ofd.zw;

    // fetch and blend
    vec2 b = smoothstep(0.25, 0.75, fuv);
    return mix( mix(textureGrad(samp, uva, ddxa, ddya),
                    textureGrad(samp, uvb, ddxb, ddyb), b.x),
                mix(textureGrad(samp, uvc, ddxc, ddyc),
                    textureGrad(samp, uvd, ddxd, ddyd), b.x), b.y);
}
''')

    def textureNoTile2DArray(self, code):
        code.append(
'''vec4 textureNoTile2DArray(sampler2DArray samp, in vec3 uv)
{
    vec2 iuv = floor(uv.xy);
    vec2 fuv = fract(uv.xy);

    // generate per-tile transform
    vec4 ofa = hash4(iuv + vec2(0.0, 0.0));
    vec4 ofb = hash4(iuv + vec2(1.0, 0.0));
    vec4 ofc = hash4(iuv + vec2(0.0, 1.0));
    vec4 ofd = hash4(iuv + vec2(1.0, 1.0));

    vec2 ddx = dFdx(uv.xy);
    vec2 ddy = dFdy(uv.xy);

    // transform per-tile uvs
    ofa.zw = sign(ofa.zw - 0.5);
    ofb.zw = sign(ofb.zw - 0.5);
    ofc.zw = sign(ofc.zw - 0.5);
    ofd.zw = sign(ofd.zw - 0.5);

    // uv's, and derivarives (for correct mipmapping)
    vec2 uva = uv.xy*ofa.zw + ofa.xy; vec2 ddxa = ddx*ofa.zw; vec2 ddya = ddy*ofa.zw;
    vec2 uvb = uv.xy*ofb.zw + ofb.xy; vec2 ddxb = ddx*ofb.zw; vec2 ddyb = ddy*ofb.zw;
    vec2 uvc = uv.xy*ofc.zw + ofc.xy; vec2 ddxc = ddx*ofc.zw; vec2 ddyc = ddy*ofc.zw;
    vec2 uvd = uv.xy*ofd.zw + ofd.xy; vec2 ddxd = ddx*ofd.zw; vec2 ddyd = ddy*ofd.zw;

    // fetch and blend
    vec2 b = smoothstep(0.25, 0.75, fuv);
    return mix( mix(textureGrad(samp, vec3(uva, uv.z), ddxa, ddya),
                    textureGrad(samp, vec3(uvb, uv.z), ddxb, ddyb), b.x),
                mix(textureGrad(samp, vec3(uvc, uv.z), ddxc, ddyc),
                    textureGrad(samp, vec3(uvd, uv.z), ddxd, ddyd), b.x), b.y);
}''')

    def extra(self, code):
        self.shader.fragment_shader.add_function(code, 'hash4', self.hash4)
        self.shader.fragment_shader.add_function(code, 'textureNoTile2D', self.textureNoTile2D)
        self.shader.fragment_shader.add_function(code, 'textureNoTile2DArray', self.textureNoTile2DArray)
