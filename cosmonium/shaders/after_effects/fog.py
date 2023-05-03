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


class Fog(ShaderComponent):

    fragment_requires = {'world_vertex'}

    def __init__(self, fall_off, density, ground):
        ShaderComponent.__init__(self)
        self.fog_fall_off = fall_off
        self.fog_density = density
        self.fog_ground = ground
        self.fog_color = (0.5, 0.6, 0.7, 1.0)
        self.sun_color = (1.0, 0.9, 0.7, 1.0)

    def get_id(self):
        return "fog"

    def fragment_uniforms(self, code):
        code.append("uniform vec3 camera;")
        code.append("uniform float fogFallOff;")
        code.append("uniform float fogDensity;")
        code.append("uniform float fogGround;")
        code.append("uniform vec4 fogColor;")
        code.append("uniform vec4 sunColor;")

    def applyFog(self, code):
        code.append('''
vec3 applyFog(in vec3  pixelColor, in vec3 position)
{
    float cam_distance = abs(distance(camera, position));
    vec3 cam_to_point = normalize(position - camera);
    //float fogAmount = 1.0 - exp(-cam_distance * fogFallOff);
    float fogAmount = fogDensity / fogFallOff * exp(-(camera.z - fogGround) * fogFallOff) * (1.0 - exp(-cam_distance * cam_to_point.z * fogFallOff )) / cam_to_point.z;
    //float fogAmount = fogDensity / fogFallOff * (exp(-(camera.z - fogGround) * fogFallOff) - exp(-(camera.z - fogGround + cam_distance * cam_to_point.z) * fogFallOff )) / cam_to_point.z;
    float sunAmount = max( dot( cam_to_point, light_dir ), 0.0 );
    vec3  mixColor = mix( fogColor.xyz, sunColor.xyz, pow(sunAmount, 8.0));
    return mix(pixelColor, mixColor, clamp(fogAmount, 0, 1));
}
''')

    def fragment_extra(self, code):
        self.applyFog(code)

    def fragment_shader(self, code):
        code.append('    total_color.xyz = applyFog(total_color.xyz, world_vertex);')

    def update_shader_shape_static(self, shape, appearance):
        shape.instance.set_shader_input("fogFallOff", self.fog_fall_off)
        shape.instance.set_shader_input("fogDensity", self.fog_density)
        shape.instance.set_shader_input("fogGround", self.fog_ground)
        shape.instance.set_shader_input("fogColor", self.fog_color)
        shape.instance.set_shader_input("sunColor", self.sun_color)