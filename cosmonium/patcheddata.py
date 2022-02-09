#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2021 Laurent Deru.
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


from panda3d.core import LVector2

from .datasource import DataSource
from .textures import TexCoord

class PatchData:
    def __init__(self, parent, patch, width, height, overlap):
        self.parent = parent
        self.patch = patch
        self.width = width
        self.height = height
        self.overlap = overlap
        self.r_width = self.width - self.overlap * 2
        self.r_height = self.height - self.overlap * 2
        self.r_x0 = patch.x0 - overlap / self.r_width * (patch.x1 - patch.x0)
        self.r_x1 = patch.x1 + overlap / self.r_width * (patch.x1 - patch.x0)
        self.r_y0 = patch.y0 - overlap / self.r_height * (patch.y1 - patch.y0)
        self.r_y1 = patch.y1 + overlap / self.r_height * (patch.y1 - patch.y0)
        self.lod = None
        self.parent_data = None
        self.data_ready = False
        self.texture = None
        self.cloned = False
        self.loaded = False
        self.texture_offset = LVector2((self.overlap + 0.5) / self.width, (self.overlap + 0.5) / self.height)
        self.texture_scale = LVector2((self.width - self.overlap * 2 - 1) / self.width, (self.height - self.overlap * 2 - 1) / self.height)

    def copy_from(self, parent_data):
        self.cloned = True
        self.lod = parent_data.lod
        self.texture = parent_data.texture
        self.data_ready = parent_data.data_ready

    def calc_sub_patch(self):
        if self.parent_data is None:
            print("No parent data", self.patch.str_id())
            return
        self.copy_from(self.parent_data)
        delta = self.patch.lod - self.lod
        scale = 1 << delta
        #TODO: This should be moved into the patch
        if self.patch.coord == TexCoord.Cylindrical:
            x_tex = (self.patch.x // scale) * scale
            y_tex = (self.patch.y // scale) * scale
            x_delta = (self.patch.x - x_tex) / scale
            y_delta = (self.patch.y - y_tex) / scale
        elif self.patch.coord != TexCoord.Flat:
            x_tex = (self.patch.x // scale) * scale
            y_tex = (self.patch.y // scale) * scale
            x_delta = (self.patch.x - x_tex) / scale
            y_delta = (self.patch.y - y_tex) / scale
        else:
            x_delta = (self.patch.x - self.parent_data.patch.x) / self.parent_data.patch.size
            y_delta = (self.patch.y - self.parent_data.patch.y) / self.parent_data.patch.size
        r_scale_x = (self.width - self.overlap * 2 - 1) / self.width
        r_scale_y = (self.height - self.overlap * 2 - 1) / self.height
        self.texture_offset = LVector2((self.overlap + 0.5) / self.width + x_delta * r_scale_x, (self.overlap + 0.5) / self.height + y_delta * r_scale_y)
        self.texture_scale = LVector2(r_scale_x / scale, r_scale_y / scale)

    def is_ready(self):
        return self.data_ready

    async def load(self, tasks_tree, patch):
        pass

    def apply(self, instance):
        pass

    def clear(self, instance):
        self.texture = None
        self.data_ready = False
        self.loaded = False
        self.cloned = False

    def retrieve_texture_data(self):
        pass

    def make_default_data(self):
        return None

    def configure_data(self, texture):
        if texture is not None:
            self.texture = texture
            self.retrieve_texture_data()
            self.data_ready = True
            self.lod = self.patch.lod
            self.texture_offset = LVector2((self.overlap + 0.5) / self.width, (self.overlap + 0.5) / self.height)
            self.texture_scale = LVector2((self.width - self.overlap * 2 - 1) / self.width, (self.height - self.overlap * 2 - 1) / self.height)
            self.cloned = False
            self.loaded = True
        else:
            if self.parent_data is not None:
                if not self.cloned:
                    self.calc_sub_patch()
            else:
                print("Make default data")
                self.configure_data(self.make_default_data())

class PatchedData(DataSource):
    def __init__(self, name, size, overlap, max_lod=100):
        self.name = name
        self.size = size
        self.overlap = overlap
        self.max_lod = max_lod
        self.map_patch_data = {}

    def get_texture_offset(self, patch):
        return self.map_patch_data[patch.str_id()].texture_offset

    def get_texture_scale(self, patch):
        return self.map_patch_data[patch.str_id()].texture_scale

    def get_patch_data(self, patch, recurse=False):
        if recurse:
            while patch is not None:
                patch_data = self.map_patch_data.get(patch.str_id(), None)
                if patch_data is not None: break
                patch = patch.parent
        else:
            patch_data = self.map_patch_data.get(patch.str_id(), None)
        return patch_data

    def do_create_patch_data(self, patch):
        pass

    def create(self, patch):
        if patch.str_id() in self.map_patch_data: return
        patch_data = self.do_create_patch_data(patch)
        self.map_patch_data[patch.str_id()] = patch_data
        parent = patch.parent
        # The parent data is also used for early display of the patch
        while parent is not None:
            parent_data = self.map_patch_data.get(parent.str_id())
            if parent_data is not None and not parent_data.cloned:
                patch_data.parent_data = parent_data
                break
            parent = parent.parent
        if patch_data.parent_data is None and patch.lod > 0:
            print("NO PARENT DATA FOR", patch.str_id())

    def create_load_task(self, tasks_tree, patch, owner):
        tasks_tree.add_task_for(self, self.load(tasks_tree, patch, owner))

    async def load(self, tasks_tree, patch, owner):
        if patch.str_id() in self.map_patch_data:
            patch_data = self.map_patch_data[patch.str_id()]
            if not patch_data.loaded:
                if patch.lod > self.max_lod:
                    patch_data.calc_sub_patch()
                    # Mark the patch data as loaded as it's beyond max lod
                    patch_data.loaded = True
                else:
                    await patch_data.load(tasks_tree, patch)
        else:
            print("PATCH NOT CREATED?", patch.str_id())

    def apply(self, patch, instance):
        if patch.str_id() in self.map_patch_data:
            patch_data = self.map_patch_data[patch.str_id()]
            patch_data.apply(instance)
        else:
            print("PATCH NOT CREATED?", patch.str_id())

    def get_nb_shader_data(self):
        raise NotImplementedError()

    def collect_shader_data(self, data, patch):
        if patch.str_id() in self.map_patch_data:
            patch_data = self.map_patch_data[patch.str_id()]
            patch_data.collect_shader_data(data)
        else:
            print("PATCH NOT CREATED?", patch.str_id())

    def clear(self, patch, instance):
        try:
            patch_data = self.map_patch_data[patch.str_id()]
            patch_data.clear(instance)
            del self.map_patch_data[patch.str_id()]
        except KeyError:
            pass

    def clear_all(self):
        self.map_patch_data = {}
