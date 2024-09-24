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

from .component import ShaderComponent


class PointControl(ShaderComponent):

    def fragment_shader_decl(self, code):
        for i in range(self.shader.nb_textures_coord):
            code.append("vec4 texcoord%i = vec4(gl_PointCoord, 0, 0);" % i)


class NoPointControl(ShaderComponent):
    pass


class StaticSizePointControl(PointControl):

    def get_id(self):
        return "pt-sta"

    def vertex_inputs(self, code):
        code.append("in float size;")

    def vertex_shader(self, code):
        code.append("gl_PointSize = size;")


class DistanceSizePointControl(PointControl):

    def get_id(self):
        return "pt-dist"

    def vertex_uniforms(self, code):
        code.append("uniform float near_plane_height;")

    def vertex_inputs(self, code):
        code.append("in float size;")

    def vertex_shader(self, code):
        code.append("gl_PointSize = (size * near_plane_height) / gl_Position.w;")
