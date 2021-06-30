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


class DataSource:
    def __init__(self, name):
        self.name = name

    def create_patch_data(self, patch):
        pass

    def create_load_patch_data_task(self, tasks_tree, patch, owner):
        pass

    async def load_patch_data(self, patch, owner):
        pass

    def apply_patch_data(self, patch, instance):
        pass

    def clear_patch(self, patch):
        pass

    def clear_all(self):
        pass

    def create_load_task(self, tasks_tree, shape, owner):
        pass

    async def load(self, shape, owner):
        pass

    def apply(self, shape, instance):
        pass
