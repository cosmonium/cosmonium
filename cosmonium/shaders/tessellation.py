#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2024 Laurent Deru.
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


from .vertex_input import VertexInput
from .component import ShaderComponent


class QuadTessellationVertexInput(VertexInput):
    def __init__(self, invert_v=False):
        VertexInput.__init__(self)
        self.invert_v = invert_v

    def vertex_layout(self, code):
        code.append("layout(quads, equal_spacing, ccw) in;")
        if self.config.vertex_shader.version < 400:
            code.append("#extension GL_ARB_tessellation_shader : enable")

    def interpolate(self, code):
        code += ['''
vec4 interpolate(in vec4 v0, in vec4 v1, in vec4 v2, in vec4 v3)
{
    vec4 a = mix(v0, v1, gl_TessCoord.x);
    vec4 b = mix(v3, v2, gl_TessCoord.x);
    return mix(a, b, gl_TessCoord.y);
}
''']

    def vertex_extra(self, code):
        self.interpolate(code)

    def vertex_shader(self, code):
        code += ['''
            model_vertex4 = interpolate(
                              gl_in[0].gl_Position,
                              gl_in[1].gl_Position,
                              gl_in[2].gl_Position,
                              gl_in[3].gl_Position);
''']
        #TODO: Retrieve normals from tesselator
        if 'model_normal' in self.config.vertex_requires:
            code.append("model_normal4 = vec4(0.0, 0.0, 1.0, 0.0);")
        if 'tangent' in self.config.vertex_requires:
            code.append("model_binormal4 = vec4(1.0, 0.0, 0.0, 0.0);")
            code.append("model_tangent4 = vec4(0.0, 1.0, 0.0, 0.0);")
        for i in range(self.config.nb_textures_coord):
            if self.invert_v:
                code.append("model_texcoord%i = vec4(gl_TessCoord.x, 1.0 - gl_TessCoord.y, 0.0, 0.0);" % (i))
            else:
                code.append("model_texcoord%i = vec4(gl_TessCoord.x, gl_TessCoord.y, 0.0, 0.0);" % (i))


class TessellationControl(ShaderComponent):
    pass


class ConstantTessellationControl(TessellationControl):
    def __init__(self, invert_v=False):
        TessellationControl.__init__(self)
        #invert_v is not used in TessellationControl but in QuadTessellationVertexInput
        #It is configured here as this is the user class
        self.invert_v = invert_v

    def get_id(self):
        return "ctess"

    def vertex_layout(self, code):
        code.append("layout(vertices = 4) out;")
        if self.shader.vertex_shader.version < 400:
            code.append("#extension GL_ARB_tessellation_shader : enable")

    def vertex_uniforms(self, code):
        code.append("uniform float TessLevelInner;")
        code.append("uniform vec4 TessLevelOuter;")

    def vertex_shader(self, code):
        code += ['''
        gl_TessLevelOuter[0] = TessLevelOuter[0];
        gl_TessLevelOuter[1] = TessLevelOuter[1];
        gl_TessLevelOuter[2] = TessLevelOuter[2];
        gl_TessLevelOuter[3] = TessLevelOuter[3];

        gl_TessLevelInner[0] = TessLevelInner;
        gl_TessLevelInner[1] = TessLevelInner;
''']
