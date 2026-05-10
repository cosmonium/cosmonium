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


from ..appearances import AppearanceBase
from .shaders import DetailMap, TextureDictionaryShaderDataSource


class ProceduralAppearance(AppearanceBase):
    def __init__(self, texture_control, texture_source, heightmap):
        AppearanceBase.__init__(self)
        self.texture_control = texture_control
        self.texture_source = texture_source
        self.appearance_source = TextureDictionaryShaderDataSource(texture_source)
        self.shader_appearance = DetailMap(texture_control, heightmap, create_normals=True)

    def get_data_source(self):
        return self.appearance_source

    def get_shader_appearance(self):
        return self.shader_appearance

    def create_load_task(self, tasks_tree, shape, owner):
        tasks_tree.add_task_for(self, self.load(tasks_tree, shape, owner))

    async def load(self, tasks_tree, shape, owner):
        await self.texture_source.load(tasks_tree, shape, owner)

    def early_apply(self, shape, instance):
        self.texture_source.apply(shape, instance)

    def apply(self, shape, instance):
        self.texture_source.apply(shape, instance)

    def clear(self, patch, instance):
        self.texture_source.clear(patch, instance)

    def clear_all(self):
        self.texture_source.clear_all()

    def update_lod(self, shape, apparent_radius, distance_to_obs, pixel_size):
        self.texture_source.update_lod(shape, apparent_radius, distance_to_obs, pixel_size)
