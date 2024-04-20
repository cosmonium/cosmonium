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


from ..base import ShaderProgram


class DefaultPassThroughVertexShader(ShaderProgram):
    def __init__(self, config):
        ShaderProgram.__init__(self, 'vertex')
        self.config = config

    def create_inputs(self, code):
        code.append("in vec4 p3d_Vertex;")

    def create_body(self, code):
        code.append("gl_Position = vec4(p3d_Vertex.xz, 0, 1);")


class TexturePassThroughVertexShader(ShaderProgram):
    def __init__(self, config):
        ShaderProgram.__init__(self, 'vertex')
        self.config = config

    def create_uniforms(self, code):
        code.append("uniform mat4x4 p3d_ModelViewProjectionMatrix;")

    def create_inputs(self, code):
        code.append("in vec4 p3d_Vertex;")

    def create_outputs(self, code):
        code.append("out vec4 uv;")

    def create_body(self, code):
        code.append("gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;")
        code.append("uv = gl_Position * 0.5 + 0.5;")


class GeomPassThroughVertexShader(ShaderProgram):
    def __init__(self, config):
        ShaderProgram.__init__(self, 'vertex')
        self.config = config

    def create_inputs(self, code):
        code.append("in vec4 p3d_Vertex;")
        code.append("in vec4 p3d_Normal;")

    def create_outputs(self, code):
        code.append("out vec4 normal;")

    def create_body(self, code):
        code.append("gl_Position = p3d_Vertex;")
        code.append("normal = p3d_Normal;")


class ColorPassThroughFragmentShader(ShaderProgram):
    def __init__(self, config):
        ShaderProgram.__init__(self, 'fragment')
        self.config = config

    def create_inputs(self, code):
        code.append("in vec4 pixel_color;")

    def create_outputs(self, code):
        code.append("out vec4 color;")

    def create_extra(self, code):
        self.add_function(code, 'to_srgb', self.to_srgb)

    def create_body(self, code):
        code.append("vec4 final_color = pixel_color;")
        if self.config.gamma_correction:
            #code.append("color = vec4(pow(final_color.xyz, vec3(1.0/2.2)), final_color.a);")
            code.append("color = vec4(to_srgb(final_color.x), to_srgb(final_color.y), to_srgb(final_color.z), final_color.a);")
        else:
            code.append("color = final_color;")


class TexturePassThroughFragmentShader(ShaderProgram):
    def __init__(self, config):
        ShaderProgram.__init__(self, 'fragment')
        self.config = config

    def create_uniforms(self, code):
        code.append("uniform sampler2D color_buffer;")
        if self.config.hdr:
            code.append("uniform float exposure;")

    def create_inputs(self, code):
        code.append("in vec4 uv;")

    def create_outputs(self, code):
        code.append("out vec4 color;")

    def create_extra(self, code):
        self.add_function(code, 'to_srgb', self.to_srgb)

    def create_body(self, code):
        code.append("vec4 final_color = texture(color_buffer, uv.xy);")
        if self.config.hdr:
            code.append("final_color = 1.0 - exp(final_color * -exposure);")
        if self.config.gamma_correction:
            #code.append("color = vec4(pow(final_color.xyz, vec3(1.0/2.2)), final_color.a);")
            code.append("color = vec4(to_srgb(final_color.x), to_srgb(final_color.y), to_srgb(final_color.z), final_color.a);")
        else:
            code.append("color = final_color;")
