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


class ShaderComponent(object):

    vertex_requires = set()
    vertex_provides = set()

    fragment_requires = set()
    fragment_provides = set()

    def __init__(self):
        self.shader = None

    def set_shader(self, shader):
        self.shader = shader

    def get_id(self):
        return ""

    def create_shader_configuration(self, appearance):
        pass

    def define_shader(self, shape, appearance):
        pass

    def get_user_parameters(self):
        return None

    def vertex_layout(self, code):
        pass

    def vertex_uniforms(self, code):
        pass

    def vertex_inputs(self, code):
        pass

    def vertex_outputs(self, code):
        pass

    def vertex_extra(self, code):
        pass

    def vertex_shader_decl(self, code):
        pass

    def vertex_shader(self, code):
        pass

    def fragment_uniforms(self, code):
        pass

    def fragment_inputs(self, code):
        pass

    def fragment_extra(self, code):
        pass

    def fragment_shader_decl(self, code):
        pass

    def fragment_shader_distort_coord(self, code):
        pass

    def fragment_shader(self, code):
        pass
