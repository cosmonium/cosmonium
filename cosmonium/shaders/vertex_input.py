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


from .component import ShaderComponent


class VertexInput(ShaderComponent):
    def __init__(self):
        ShaderComponent.__init__(self)
        self.config = None

    def set_shader(self, shader):
        ShaderComponent.set_shader(self, shader)
        self.config = shader

class DirectVertexInput(VertexInput):
    def vertex_inputs(self, code):
        code.append("in vec4 p3d_Vertex;")
        if self.config.use_normal or self.config.vertex_control.use_normal:
            code.append("in vec4 p3d_Normal;")
        if self.config.use_tangent:
            code.append("in vec4 p3d_Binormal;")
            code.append("in vec4 p3d_Tangent;")
        for i in range(self.config.nb_textures_coord):
            code.append("in vec4 p3d_MultiTexCoord%i;" % i)

    def vertex_shader(self, code):
        code.append("model_vertex4 = p3d_Vertex;")
        if self.config.use_normal or self.config.vertex_control.use_normal:
            code.append("model_normal4 = vec4(p3d_Normal.xyz, 0.0);")
        if self.config.use_tangent:
            code.append("model_tangent4 = vec4(p3d_Tangent.xyz, 0.0);")
            if self.config.generate_binormal:
                #TODO: Should be done here ?
                code.append("model_binormal4 = vec4(cross(p3d_Normal.xyz, p3d_Tangent.xyz) * p3d_Tangent.w, 0.0);")
            else:
                code.append("model_binormal4 = vec4(p3d_Binormal.xyz, 0.0);")
        if self.config.use_model_texcoord:
            for i in range(self.config.nb_textures_coord):
                code.append("model_texcoord%i = p3d_MultiTexCoord%i;" % (i, i))
        else:
            #TODO: Should be done here ?
            code.append("vec3 tmp = model_vertex4.xyz / model_vertex4.w;")
            code.append("float tmp_len = length(tmp);")
            code.append("float u = atan(tmp.y, tmp.x) / pi / 2 + 0.5;")
            code.append("float v = asin(tmp.z / tmp_len) / pi + 0.5;")
            code.append("model_texcoord0 = vec4(fract(u), v, 0, 1);")
            code.append("model_texcoord0p = vec4(fract(u + 0.5) - 0.5, v, 0, 1);")
