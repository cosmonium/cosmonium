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


from ..base import ShaderProgram, StructuredShader
from .passthrough import GeomPassThroughVertexShader, ColorPassThroughFragmentShader

class GenerateNormalsGeomShader(ShaderProgram):
    def create_layout(self, code):
        code.append("layout(triangles) in;")
        code.append("layout(line_strip, max_vertices=6) out;")

    def create_uniforms(self, code):
        code.append("uniform mat4x4 p3d_ModelViewProjectionMatrix;")
        code.append("vec4 normal_color;")
        code.append("float normal_length;")

    def create_inputs(self, code):
        code.append("in normal[];")

    def create_outputs(self, code):
        code.append("out pixel_color;")

    def create_body(self, code):
        code.append("int i;")
        code.append("for(i=0; i<gl_in.length(); i++)")
        code.append("{")
        code.append("  vec3 cur_vertex = gl_in[i].gl_Position.xyz;")
        code.append("  vec3 cur_normal = normal[i].xyz;")
        code.append("  gl_Position = p3d_ModelViewProjectionMatrix * vec4(cur_vertex, 1.0);")
        code.append("  pixel_color = normal_color;")
        code.append("  EmitVertex();")
        code.append("  gl_Position = p3d_ModelViewProjectionMatrix * vec4(cur_vertex + cur_normal * normal_length, 1.0);")
        code.append("  pixel_color = normal_color;")
        code.append("  EmitVertex();")
        code.append("  EndPrimitive();")
        code.append("}")

class DebugNormalsShader(StructuredShader):
    def __init__(self):
        self.geometry_shader = GenerateNormalsGeomShader(self)
        self.vertex_shader = GeomPassThroughVertexShader(self)
        self.fragment_shader = ColorPassThroughFragmentShader(self)

    def get_shader_id(self):
        return "normals"
