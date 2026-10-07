#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2026 Laurent Deru.
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


import builtins
import logging
import struct
from collections import deque

from panda3d.core import GeomEnums, ShaderBuffer, Texture

from ..opengl import OpenGLConfig
from ..shaders.data_source.data_store import DataStoreManagerShaderDataSource, ParametersDataStoreShaderDataSource

logger = logging.getLogger('data_store')


class PatchDataStoreManager:
    def __init__(self, max_elem):
        self.max_elem = max_elem
        self.entries = [None] * max_elem
        self.free_entries = deque(range(max_elem))
        self.data_stores = []
        self.parameters = PatchParametersDataStore()
        self.add_data_store(self.parameters)

    def add_data_store(self, data_store):
        self.data_stores.append(data_store)
        data_store.parent = self

    def init(self):
        for data_store in self.data_stores:
            data_store.init()

    def get_shader_data_source(self):
        shader_data_source = DataStoreManagerShaderDataSource()
        for data_store in self.data_stores:
            shader_data_source.add_source(data_store.get_shader_data_source())
        return shader_data_source

    def apply(self, instance):
        for data_store in self.data_stores:
            data_store.apply(instance)

    def clear(self):
        self.entries = [None] * self.max_elem
        self.free_entries = deque(range(self.max_elem))
        for data_store in self.data_stores:
            data_store.clear()

    def apply_patch_data(self, patch, instance):
        if patch.entry_id is None:
            self.add_patch(patch)
        instance.set_shader_input('entry_id', patch.entry_id)

    def add_patch(self, patch):
        if patch.entry_id is None:
            entry_id = self.free_entries.pop()
            patch.entry_id = entry_id

    def remove_patch(self, patch):
        entry_id = patch.entry_id
        if entry_id is not None:
            self.free_entries.append(entry_id)
            patch.entry_id = None

    def update_patch(self, patch):
        if patch.entry_id is None:
            self.add_patch(patch)
        for data_store in self.data_stores:
            data_store.update_patch(patch)


class PatchParametersDataStore:
    def __init__(self):
        self.use_shader_buffer = OpenGLConfig.shader_buffer
        self.texture_data = None
        self.shader_buffer = None
        self.data_sources = []
        self.data_size = 0
        self.stride = 0
        self.pack_format = ''

    def get_shader_data_source(self):
        return ParametersDataStoreShaderDataSource(self)

    def is_initialized(self):
        return self.texture_data is not None or self.shader_buffer is not None

    def add_data_source(self, data_source):
        if self.is_initialized():
            logger.error("Can not add data source '%s'", data_source.name)
            return
        self.data_sources.append(data_source)
        self.data_size += data_source.get_nb_shader_data()
        # Each entry is stored as an array of vec4
        self.stride = (self.data_size + 3) // 4
        self.pack_format = 'f' * self.stride * 4

    def init(self):
        if self.stride == 0:
            return
        nb_vec4 = self.parent.max_elem * self.stride
        if self.use_shader_buffer:
            self.shader_buffer = ShaderBuffer('data_store', bytes(nb_vec4 * 16), GeomEnums.UH_dynamic)
        else:
            self.texture_data = Texture()
            self.texture_data.setup_1d_texture(nb_vec4, Texture.T_float, Texture.F_rgba32)
            self.texture_data.set_clear_color(0.0)

    def apply(self, instance):
        if self.use_shader_buffer:
            if self.shader_buffer is not None:
                instance.set_shader_input("DataStoreBuffer", self.shader_buffer)
        else:
            if self.texture_data is not None:
                instance.set_shader_input("data_store", self.texture_data)

    def clear(self):
        self.texture_data = None
        self.shader_buffer = None

    def update_patch(self, patch):
        if not self.is_initialized():
            return
        data = []
        for data_source in self.data_sources:
            data_source.collect_shader_data(data, patch)
        data += [0.0] * (self.stride * 4 - len(data))
        offset = patch.entry_id * self.stride * 16
        if self.use_shader_buffer:
            packed_data = struct.pack(self.pack_format, *data)
            builtins.base.graphics_engine.update_shader_buffer_data(
                self.shader_buffer, builtins.base.win.gsg, packed_data, offset
            )
        else:
            # Texture data is stored as BGRA, swap the R and B components of each vec4
            for i in range(0, len(data), 4):
                data[i], data[i + 2] = data[i + 2], data[i]
            packed_data = struct.pack(self.pack_format, *data)
            data_buffer = memoryview(self.texture_data.modify_ram_image())
            data_buffer[offset : offset + len(packed_data)] = packed_data
