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


from direct.task.Task import gather


class DataSourceTasksTree:
    def __init__(self, sources):
        self.sources = sources
        self.named_tasks = {source.name: None for source in sources}
        self.tasks = []

    def add_task_for(self, source, coro):
        task = taskMgr.add(coro)
        self.named_tasks[source.name] = task
        self.tasks.append(task)

    def collect_patch_tasks(self, patch, owner):
        for source in self.sources:
            source.create_load_patch_data_task(self, patch, owner)

    def collect_tasks(self, shape, owner):
        for source in self.sources:
            source.create_load_task(self, shape, owner)

    async def run_tasks(self):
        await gather(*self.tasks)
        self.named_tasks = {}
        self.tasks = []


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

    def update(self, shape, instance, camera_pos, camera_rot):
        pass

    def clear_shape_data(self, shape, instance):
        pass

    def get_user_parameters(self):
        return None

    def update_user_parameters(self):
        pass

class DataSourcesHandler:
    def __init__(self):
        self.sources = []

    def add_source(self, source):
        self.sources.append(source)

    def remove_source(self, source):
        self.sources.remove(source)

    def remove_source_by_name(self, name):
        source = None
        for source in self.sources:
            if source.name == name:
                self.sources.remove(source)
                break

    async def load_patch_data(self, patch):
        for source in self.sources:
            source.create_patch_data(patch)
        tasks_tree = DataSourceTasksTree(self.sources)
        tasks_tree.collect_patch_tasks(patch, self)
        await tasks_tree.run_tasks()

    def apply_patch_data(self, patch):
        for source in self.sources:
            source.apply_patch_data(patch, patch.instance)

    def early_apply_patch_data(self, patch):
        for source in self.sources:
            source.create_patch_data(patch)
            source.apply_patch_data(patch, patch.instance)

    async def load_shape_data(self, shape):
        tasks_tree = DataSourceTasksTree(self.sources)
        tasks_tree.collect_tasks(shape, self)
        await tasks_tree.run_tasks()

    def apply_shape_data(self, shape):
        for source in self.sources:
            source.apply(shape, shape.instance)

    def update_shape_data(self, shape, camera_pos, camera_rot):
        for source in self.sources:
            source.update(shape, shape.instance, camera_pos, camera_rot)

    def clear_shape_data(self, shape, instance):
        for source in self.sources:
            source.clear_shape_data(shape, shape.instance)
