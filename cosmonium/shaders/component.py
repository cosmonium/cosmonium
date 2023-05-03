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


from __future__ import annotations


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


class CompositeShaderComponent(ShaderComponent):
    def __init__(self):
        ShaderComponent.__init__(self)
        self.components: list[ShaderComponent] = []
        self.fragment_provides = set()
        self.fragment_requires = set()
        self.vertex_provides = set()
        self.vertex_requires = set()

    def add_component(self, component: ShaderComponent):
        self.components.append(component)
        component.set_shader(self.shader)
        self.fragment_provides.update(component.fragment_provides)
        self.fragment_requires.update(component.fragment_requires)
        self.vertex_provides.update(component.vertex_provides)
        self.vertex_requires.update(component.vertex_requires)

    def remove_component(self, component: ShaderComponent):
        self.components.remove(component)
        component.set_shader(None)
        self.fragment_provides = set()
        self.fragment_requires = set()
        self.vertex_provides = set()
        self.vertex_requires = set()
        for component in self.components:
            self.fragment_provides.update(component.fragment_provides)
            self.fragment_requires.update(component.fragment_requires)
            self.vertex_provides.update(component.vertex_provides)
            self.vertex_requires.update(component.vertex_requires)

    def set_shader(self, shader):
        self.shader = shader
        for component in self.components:
            component.set_shader(shader)

    def get_id(self):
        return '-'.join([component.get_id() for component in self.components])

    def create_shader_configuration(self, appearance):
        for component in self.components:
            component.create_shader_configuration(appearance)

    def define_shader(self, shape, appearance):
        for component in self.components:
            component.define_shader(shape, appearance)

    def get_user_parameters(self):
        return None

    def vertex_layout(self, code):
        for component in self.components:
            component.vertex_layout(code)

    def vertex_uniforms(self, code):
        for component in self.components:
            component.vertex_uniforms(code)

    def vertex_inputs(self, code):
        for component in self.components:
            component.vertex_inputs(code)

    def vertex_outputs(self, code):
        for component in self.components:
            component.vertex_outputs(code)

    def vertex_extra(self, code):
        for component in self.components:
            component.vertex_extra(code)

    def vertex_shader_decl(self, code):
        for component in self.components:
            component.vertex_shader_decl(code)

    def vertex_shader(self, code):
        for component in self.components:
            component.vertex_shader(code)

    def fragment_uniforms(self, code):
        for component in self.components:
            component.fragment_uniforms(code)

    def fragment_inputs(self, code):
        for component in self.components:
            component.fragment_inputs(code)

    def fragment_extra(self, code):
        for component in self.components:
            component.fragment_extra(code)

    def fragment_shader_decl(self, code):
        for component in self.components:
            component.fragment_shader_decl(code)

    def fragment_shader_distort_coord(self, code):
        for component in self.components:
            component.fragment_shader_distort_coord(code)

    def fragment_shader(self, code):
        for component in self.components:
            component.fragment_shader(code)
