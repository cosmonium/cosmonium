#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2023 Laurent Deru.
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

from ..shaders.base import ShaderProgram


class GeneratorVertexShader(ShaderProgram):

    def __init__(self):
        ShaderProgram.__init__(self, 'vertex')

    def create_uniforms(self, code):
        code.append("uniform mat4 p3d_ModelViewProjectionMatrix;")

    def create_inputs(self, code):
        code.append("in vec2 p3d_MultiTexCoord0;")
        code.append("in vec4 p3d_Vertex;")

    def create_outputs(self, code):
        code.append("out vec2 texcoord;")

    def create_body(self, code):
        code.append("gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;")
        code.append("texcoord = p3d_MultiTexCoord0;")
