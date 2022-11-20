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


from panda3d.core import LVector2, AsyncFuture

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
        self.data_ready = False
        self.texture = None
        self.data_patch = patch
        self.data_lod = None
        self.loaded = False
        self.texture_offset = None
        self.texture_scale = None
        self.awaitables = []

    def copy_from(self, parent_data):
        self.texture = parent_data.texture
        self.data_lod = parent_data.data_lod
        self.data_ready = parent_data.data_ready
        self.data_patch = parent_data.patch

    def calc_scale_and_offset(self, shape_patch):
        delta = shape_patch.lod - self.data_lod
        scale = 1 << delta
        #TODO: This should be moved into the patch
        if shape_patch.coord == TexCoord.Cylindrical:
            x_tex = (shape_patch.x // scale) * scale
            y_tex = (shape_patch.y // scale) * scale
            x_delta = (shape_patch.x - x_tex) / scale
            y_delta = (shape_patch.y - y_tex) / scale
        elif shape_patch.coord != TexCoord.Flat:
            x_tex = (shape_patch.x // scale) * scale
            y_tex = (shape_patch.y // scale) * scale
            x_delta = (shape_patch.x - x_tex) / scale
            y_delta = (shape_patch.y - y_tex) / scale
        else:
            x_delta = (shape_patch.x - self.data_patch.x) / self.data_patch.size
            y_delta = (shape_patch.y - self.data_patch.y) / self.data_patch.size
        r_scale_x = (self.width - self.overlap * 2) / self.width
        r_scale_y = (self.height - self.overlap * 2) / self.height
        texture_offset = LVector2(self.overlap / self.width + x_delta * r_scale_x, self.overlap / self.height + y_delta * r_scale_y)
        texture_scale = LVector2(r_scale_x / scale, r_scale_y / scale)
        return texture_offset, texture_scale

    def calc_sub_patch(self, parent_data):
        self.copy_from(parent_data)
        self.texture_offset, self.texture_scale = self.calc_scale_and_offset(self.patch)

    def is_ready(self):
        return self.data_ready

    def is_waiting(self):
        for awaitable in self.awaitables:
            if not awaitable.cancelled():
                return True
        return False

    def load(self, tasks_tree, patch):
        if len(self.awaitables) == 0:
            task = taskMgr.add(self.load_wrapper(tasks_tree, patch))
        future = AsyncFuture()
        self.awaitables.append(future)
        return future

    async def load_wrapper(self, tasks_tree, patch):
        result = await self.do_load(tasks_tree, patch)
        for awaitable in self.awaitables:
            if not awaitable.cancelled():
                awaitable.set_result(result)
        self.awaitables = []

    async def do_load(self, tasks_tree, patch):
        pass

    def apply(self, instance):
        pass

    def clear(self, instance):
        self.texture = None
        self.data_ready = False
        self.loaded = False

    def retrieve_texture_data(self):
        pass

    def make_default_data(self):
        return None

    def configure_data(self, texture):
        self.texture = texture
        self.retrieve_texture_data()
        self.data_ready = True
        self.data_lod = self.patch.lod
        self.texture_offset = LVector2(self.overlap / self.width, self.overlap / self.height)
        self.texture_scale = LVector2((self.width - self.overlap * 2) / self.width, (self.height - self.overlap * 2) / self.height)
        self.loaded = True

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

    def get_patch_data(self, patch, strict=False):
        if not strict:
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

    def get_or_create(self, patch):
        try:
            patch_data = self.map_patch_data[patch.str_id()]
        except KeyError:
            patch_data = self.do_create_patch_data(patch)
            self.map_patch_data[patch.str_id()] = patch_data
        return patch_data

    def early_apply(self, patch, instance):
        if patch.str_id() in self.map_patch_data:
            patch_data = self.map_patch_data[patch.str_id()]
            if not patch_data.loaded:
                parent = patch.parent
                parent_data = None
                while parent is not None:
                    parent_data = self.map_patch_data.get(parent.str_id())
                    if parent_data is not None and parent_data.loaded:
                        break
                    parent = parent.parent
                if parent_data is not None:
                    patch_data.calc_sub_patch(parent_data)
                    patch_data.apply(instance)
                else:
                    if patch.lod > 0:
                        print("NO PARENT DATA FOR", patch.str_id())
            else:
                patch_data.apply(instance)
        else:
            print("PATCH NOT CREATED?", patch.str_id())

    def create_load_task(self, tasks_tree, patch, owner):
        tasks_tree.add_task_for(self, self.load(tasks_tree, patch, owner))

    def find_max_lod_parent(self, patch_data):
        parent = patch_data.patch.parent
        while parent is not None and parent.lod != self.max_lod:
            parent = parent.parent
        if parent is not None:
            return self.get_or_create(parent)
        else:
            print("MAX LOD PATCH NOT FOUND")

    async def load(self, tasks_tree, patch, owner):
        if patch.str_id() in self.map_patch_data:
            patch_data = self.map_patch_data[patch.str_id()]
            if not patch_data.loaded:
                if patch.lod > self.max_lod:
                    max_lod_parent = self.find_max_lod_parent(patch_data)
                    if not max_lod_parent.loaded:
                        await max_lod_parent.load(tasks_tree, max_lod_parent.patch)
                    patch_data.calc_sub_patch(max_lod_parent)
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
