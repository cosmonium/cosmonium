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


class CustomShaderComponent(ShaderComponent):
    def __init__(self, component_id):
        self.component_id = component_id

        self.vertex_requires = set()
        self.vertex_provides = set()
        self.fragment_requires = set()
        self.fragment_provides = set()

        self.vertex_uniforms_data = []
        self.vertex_inputs_data = []
        self.vertex_outputs_data = []
        self.vertex_extra_data = []
        self.update_vertex_data = []
        self.update_normal_data = []
        self.vertex_shader_data = []
        self.fragment_uniforms_data = []
        self.fragment_inputs_data = []
        self.fragment_extra_data = []
        self.fragment_shader_decl_data = []
        self.fragment_shader_distort_coord_data = []
        self.fragment_shader_data = []

    def get_id(self):
        return self.component_id

    def vertex_uniforms(self, code):
        code += self.vertex_uniforms_data

    def vertex_inputs(self, code):
        code += self.vertex_inputs_data

    def vertex_outputs(self, code):
        code += self.vertex_outputs_data

    def vertex_extra(self, code):
        code += self.vertex_extra_data

    def update_vertex(self, code):
        code += self.update_vertex_data

    def update_normal(self, code):
        code += self.update_normal_data

    def vertex_shader(self, code):
        code += self.vertex_shader_data

    def fragment_uniforms(self, code):
        code += self.fragment_uniforms_data

    def fragment_inputs(self, code):
        code += self.fragment_inputs_data

    def fragment_extra(self, code):
        code += self.fragment_extra_data

    def fragment_shader_decl(self, code):
        code += self.fragment_shader_decl_data

    def fragment_shader_distort_coord(self, code):
        code += self.fragment_shader_distort_coord_data

    def fragment_shader(self, code):
        code += self.fragment_shader_data
