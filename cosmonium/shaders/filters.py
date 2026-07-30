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


class TextureFilter:
    filter_name = None
    derivatives_name = None

    def __init__(self, interpolator):
        self.interpolator = interpolator.get_data_source_interpolator()

    def get_id(self):
        raise NotImplementedError()

    def apply(self, sampler, pos):
        return f"{self.filter_name}({sampler}, {pos})"

    def derivatives(self, sampler, pos):
        return f"{self.derivatives_name}({sampler}, {pos})"

    def extra(self, shader, code):
        raise NotImplementedError()

    @property
    def has_derivatives(self) -> bool:
        return self.derivatives_name is not None


class TextureNearestFilter(TextureFilter):
    filter_name = 'texture_nearest_filter'

    def get_id(self):
        return '-n'

    def texture_nearest_filter(self, code):
        code += ['''
vec4 texture_nearest_filter( sampler2D sam, vec2 p )
{
    return %s;
}
''' % self.interpolator.apply('sam', 'p')]

    def extra(self, shader, code):
        shader.add_function(code, 'texture_nearest_filter', self.texture_nearest_filter)


class TextureBilinearFilter(TextureFilter):
    filter_name = 'texture_bilinear_filter'

    def get_id(self):
        return '-l'

    def texture_bilinear_filter(self, code):
        code += ['''
vec4 texture_bilinear_filter( sampler2D sam, vec2 p )
{
    return %s;
}
''' % self.interpolator.apply('sam', 'p')]

    def extra(self, shader, code):
        shader.add_function(code, 'texture_bilinear_filter', self.texture_bilinear_filter)


class TextureSmoothstepFilter(TextureFilter):
    filter_name = 'texture_smoothstep_filter'

    def get_id(self):
        return '-s'

    def texture_smoothstep_filter(self, code):
        code += ['''
vec4 texture_smoothstep_filter( sampler2D sam, vec2 p )
{
    vec2 res = textureSize( sam, 0 );
    p = p*res + 0.5;

    vec2 i = floor(p);
    vec2 f = fract(p);
    f = smoothstep(0, 1, f);  //f*f*(3.0-2.0*f);
    p = i + f;

    p = (p - 0.5)/res;
    return %s;
}
''' % self.interpolator.apply('sam', 'p')]

    def extra(self, shader, code):
        shader.add_function(code, 'texture_smoothstep_filter', self.texture_smoothstep_filter)


class TextureQuinticFilter(TextureFilter):
    filter_name = 'texture_quintic_filter'

    def get_id(self):
        return '-q'

    def texture_quintic_filter(self, code):
        code += ['''
vec4 texture_quintic_filter( sampler2D sam, vec2 p )
{
    vec2 res = textureSize( sam, 0 );
    p = p*res + 0.5;

    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f*f*f*(f*(f*6.0-15.0)+10.0);
    p = i + f;

    p = (p - 0.5)/res;
    return %s;
}
''' % self.interpolator.apply('sam', 'p')]

    def extra(self, shader, code):
        shader.add_function(code, 'texture_quintic_filter', self.texture_quintic_filter)


class TextureBSplineFilter(TextureFilter):
    filter_name = 'texture_bspline_filter'
    derivatives_name = 'texture_bspline_filter_derivatives'
    delta_width = 1

    def get_id(self):
        return '-b'

    def texture_bspline_filter(self, code):
        code += [
            '''
vec4 cubic(float alpha) {
    float alpha2 = alpha*alpha;
    float alpha3 = alpha2*alpha;
    float w0 = 1./6. * (-alpha3 + 3.*alpha2 - 3.*alpha + 1.);
    float w1 = 1./6. * (3.*alpha3 - 6.*alpha2 + 4.);
    float w2 = 1./6. * (-3.*alpha3 + 3.*alpha2 + 3.*alpha + 1.);
    float w3 = 1./6. * alpha3;
    return vec4(w0, w1, w2, w3);
}

vec4 texture_bspline_filter(sampler2D sam, vec2 pos)
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

    float p00 = %s.x;
    float p01 = %s.x;
    float p10 = %s.x;
    float p11 = %s.x;

    float a = mix(p01, p00, sx);
    float b = mix(p11, p10, sx);
    return vec4(mix(b, a, sy));
}'''
            % (
                self.interpolator.apply('sam', 'offset.xz'),
                self.interpolator.apply('sam', 'offset.yz'),
                self.interpolator.apply('sam', 'offset.xw'),
                self.interpolator.apply('sam', 'offset.yw'),
            )
        ]

    def texture_bspline_filter_derivatives(self, code):
        code += [
            '''
vec4 cubic_deriv(float alpha) {
    float alpha2 = alpha*alpha;
    float w0 = 1./6. * (-3.*alpha2 + 6.*alpha - 3.);
    float w1 = 1./6. * (9.*alpha2 -12.*alpha);
    float w2 = 1./6. * (-9.*alpha2 + 6.*alpha + 3.);
    float w3 = 1./6. * (3.*alpha2);
    return vec4(w0, w1, w2, w3);
}

vec2 texture_bspline_filter_derivatives(sampler2D sam, vec2 pos)
{
    vec2 texSize = textureSize(sam, 0);
    pos *= texSize;
    vec2 tc = floor(pos - 0.5) + 0.5;

    vec2 alpha = pos - tc;
    vec4 cubicx = cubic(alpha.x);
    vec4 cubicx_d = cubic_deriv(alpha.x);
    vec4 cubicy = cubic(alpha.y);
    vec4 cubicy_d = cubic_deriv(alpha.y);

    vec4 c = tc.xxyy + vec2 (-1., +1.).xyxy;

    vec4 s = vec4(cubicx.xz + cubicx.yw, cubicy.xz + cubicy.yw);
    vec4 s_d = vec4(cubicx_d.xz + cubicx_d.yw, cubicy_d.xz + cubicy_d.yw);
    vec4 offset = c + vec4 (cubicx.yw, cubicy.yw) / s;
    vec4 offset_d = c + vec4 (cubicx_d.yw, cubicy_d.yw) / s_d;

    offset /= texSize.xxyy;
    offset_d /= texSize.xxyy;

    float sx = s.x / (s.x + s.y);
    float sx_dx = s_d.y;
    float sy = s.z / (s.z + s.w);
    float sy_dy = s_d.w;

    float p00_dx = %s.x;
    float p01_dx = %s.x;
    float p10_dx = %s.x;
    float p11_dx = %s.x;

    float p00_dy = %s.x;
    float p01_dy = %s.x;
    float p10_dy = %s.x;
    float p11_dy = %s.x;

    float a_dx = (p01_dx - p00_dx) * sx_dx;
    float b_dx = (p11_dx - p10_dx) * sx_dx;
    float dx = mix(b_dx, a_dx, sy);

    float a = mix(p01_dy, p00_dy, sx);
    float b = mix(p11_dy, p10_dy, sx);
    float dy = (b - a) * sy_dy;
    return vec2(dx, dy);
}'''
            % (
                self.interpolator.apply('sam', 'vec2(offset_d.x, offset.z)'),
                self.interpolator.apply('sam', 'vec2(offset_d.y, offset.z)'),
                self.interpolator.apply('sam', 'vec2(offset_d.x, offset.w)'),
                self.interpolator.apply('sam', 'vec2(offset_d.y, offset.w)'),
                self.interpolator.apply('sam', 'vec2(offset.x, offset_d.z)'),
                self.interpolator.apply('sam', 'vec2(offset.y, offset_d.z)'),
                self.interpolator.apply('sam', 'vec2(offset.x, offset_d.w)'),
                self.interpolator.apply('sam', 'vec2(offset.y, offset_d.w)'),
            ),
        ]

    def extra(self, shader, code):
        shader.add_function(code, 'texture_bspline_filter', self.texture_bspline_filter)
        shader.add_function(code, 'texture_bspline_filter_derivatives', self.texture_bspline_filter_derivatives)
