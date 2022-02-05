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


from panda3d.core import Texture
from .shaders.data_source.data_store import DataStoreManagerShaderDataSource, ParametersDataStoreShaderDataSource

from collections import deque
import struct


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
        self.texture_data = None
        self.data_sources = []
        self.data_size = 0
        self.texture_size = 0
        self.pack_format = ''

    def get_shader_data_source(self):
        return ParametersDataStoreShaderDataSource()

    def add_data_source(self, data_source):
        if self.texture_data is not None:
            print("ERROR, can not add data source")
            return
        self.data_sources.append(data_source)
        self.data_size += data_source.get_nb_shader_data()
        self.texture_size = self.parent.max_elem * ((self.data_size * 4 + 15) // 16)
        self.pack_format = 'f' * self.data_size

    def init(self):
        if self.texture_size == 0: return
        self.texture_data = Texture()
        self.texture_data.setup_1d_texture(self.texture_size, Texture.T_float, Texture.F_rgba32)
        self.texture_data.set_clear_color(0.0)

    def apply(self, instance):
        if self.texture_size == 0: return
        instance.set_shader_input("data_store", self.texture_data)

    def clear(self):
        self.texture_data = None

    def update_patch(self, patch):
        if self.texture_size == 0: return
        data = []
        for data_source in self.data_sources:
            data_source.collect_shader_data(data, patch)
        data_buffer = memoryview(self.texture_data.modify_ram_image())
        offset = patch.entry_id * self.data_size * 4
        packed_data = struct.pack(self.pack_format, *data)
        data_buffer[offset : offset + self.data_size * 4] = packed_data
