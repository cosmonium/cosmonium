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


class TextureInterpolator:
    interpolator_name = None

    def get_id(self):
        raise NotImplementedError()

    def apply(self, sampler, pos):
        return f"{self.interpolator_name}({sampler}, {pos})"

    def extra(self, shader, code):
        raise NotImplementedError()


class TextureHardwareInterpolator(TextureInterpolator):
    interpolator_name = 'texture_hardware_fetch'


    def get_id(self):
        return ''

    def texture_hardware_fetch(self, code):
        code += ['''
vec4 texture_hardware_fetch( sampler2D sam, vec2 uv )
{
    return texture( sam, uv );
}
''']

    def extra(self, shader, code):
        shader.add_function(code, 'texture_hardware_fetch', self.texture_hardware_fetch)


class TextureSoftwareInterpolator(TextureInterpolator):
    interpolator_name = 'texture_software_fetch'

    def get_id(self):
        return '-sw'

    def texture_software_fetch(self, code):
        code += ['''
vec4 texture_software_fetch( sampler2D sam, vec2 uv )
{
    vec2 res = textureSize( sam, 0 );

    vec2 st = uv*res - 0.5;

    vec2 iuv = floor( st );
    vec2 fuv = fract( st );

    vec4 a = texture( sam, (iuv+vec2(0.5,0.5))/res );
    vec4 b = texture( sam, (iuv+vec2(1.5,0.5))/res );
    vec4 c = texture( sam, (iuv+vec2(0.5,1.5))/res );
    vec4 d = texture( sam, (iuv+vec2(1.5,1.5))/res );

    return mix( mix( a, b, fuv.x),
                mix( c, d, fuv.x), fuv.y );
}
''']

    def extra(self, shader, code):
        shader.add_function(code, 'texture_software_fetch', self.texture_software_fetch)
