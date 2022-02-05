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


from ..component import ShaderComponent


class ShaderDataSource(ShaderComponent):
    def has_source_for(self, source):
        return False

    def get_source_for(self, source, params=None, error=True):
        if error: print("Unknown source '%s' requested" % source)
        return ''

class CompositeShaderDataSource(ShaderDataSource):
    def __init__(self, sources=None):
        ShaderDataSource.__init__(self)
        if sources is None:
            self.sources = []
        elif isinstance(sources, list):
            self.sources = sources
        else:
            self.sources = [sources]

    def set_shader(self, shader):
        self.shader = shader
        for source in self.sources:
            source.set_shader(shader)

    def get_id(self):
        str_id = ""
        for source in self.sources:
            src_id = source.get_id()
            if src_id:
                str_id += '-'
                str_id += src_id
        return str_id

    def add_source(self, source):
        self.sources.append(source)
        source.set_shader(self.shader)

    def create_shader_configuration(self, appearance):
        for source in self.sources:
            source.create_shader_configuration(appearance)

    def has_source_for(self, source_id):
        for source in self.sources:
            if source.has_source_for(source_id):
                return True
        return False

    def get_source_for(self, source_id, params=None, error=True):
        for source in self.sources:
            value = source.get_source_for(source_id, params, False)
            if value != '':
                return value
        if error: print("Unknown source '%s' requested" % source_id)
        return ''

    def vertex_layout(self, code):
        for source in self.sources:
            source.vertex_layout(code)

    def vertex_uniforms(self, code):
        for source in self.sources:
            source.vertex_uniforms(code)

    def vertex_inputs(self, code):
        for source in self.sources:
            source.vertex_inputs(code)

    def vertex_outputs(self, code):
        for source in self.sources:
            source.vertex_outputs(code)

    def vertex_extra(self, code):
        for source in self.sources:
            source.vertex_extra(code)

    def vertex_shader_decl(self, code):
        for source in self.sources:
            source.vertex_shader_decl(code)

    def vertex_shader(self, code):
        for source in self.sources:
            source.vertex_shader(code)

    def fragment_uniforms(self, code):
        for source in self.sources:
            source.fragment_uniforms(code)

    def fragment_inputs(self, code):
        for source in self.sources:
            source.fragment_inputs(code)

    def fragment_extra(self, code):
        for source in self.sources:
            source.fragment_extra(code)

    def fragment_shader_decl(self, code):
        for source in self.sources:
            source.fragment_shader_decl(code)

    def fragment_shader_distort_coord(self, code):
        for source in self.sources:
            source.fragment_shader_distort_coord(code)

    def fragment_shader(self, code):
        for source in self.sources:
            source.fragment_shader(code)
