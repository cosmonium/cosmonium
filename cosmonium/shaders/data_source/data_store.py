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


from .base import CompositeShaderDataSource, ShaderDataSource


class DataStoreManagerShaderDataSource(CompositeShaderDataSource):
    pass


class ParametersDataStoreShaderDataSource(ShaderDataSource):
    def __init__(self, data_store):
        ShaderDataSource.__init__(self)
        self.data_store = data_store

    def get_id(self):
        if self.data_store.use_shader_buffer:
            return "ds-ssbo%d" % self.data_store.stride
        else:
            return "ds%d" % self.data_store.stride

    def uniforms(self, code):
        if self.data_store.use_shader_buffer:
            code.append("layout(std430) readonly buffer DataStoreBuffer {")
            code.append("    vec4 data_store[];")
            code.append("};")
        else:
            code.append("uniform sampler1D data_store;")
        code.append("uniform int entry_id;")

    def fetch_data_store(self, code):
        code.append("vec4 fetch_data_store(int index) {")
        if self.data_store.use_shader_buffer:
            code.append("    return data_store[entry_id * %d + index];" % self.data_store.stride)
        else:
            code.append("    return texelFetch(data_store, entry_id * %d + index, 0);" % self.data_store.stride)
        code.append("}")

    def vertex_uniforms(self, code):
        self.uniforms(code)

    def fragment_uniforms(self, code):
        self.uniforms(code)

    def vertex_extra(self, code):
        self.shader.vertex_shader.add_function(code, 'fetch_data_store', self.fetch_data_store)

    def fragment_extra(self, code):
        self.shader.fragment_shader.add_function(code, 'fetch_data_store', self.fetch_data_store)
