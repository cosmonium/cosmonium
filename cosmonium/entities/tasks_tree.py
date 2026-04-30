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


from direct.task.Task import gather
from direct.task.TaskManagerGlobal import taskMgr


class TasksTree:
    def __init__(self, sources):
        self.sources = sources
        self.named_tasks = {source.name: None for source in sources}
        self.tasks = []

    def add_task_for(self, source, coro):
        task = taskMgr.add(coro, sort=taskMgr.getCurrentTask().sort + 1)
        self.named_tasks[source.name] = task
        self.tasks.append(task)

    def collect_tasks(self, shape, owner):
        for source in self.sources:
            source.create_load_task(self, shape, owner)

    async def run_tasks(self):
        if self.tasks:
            await gather(*self.tasks)
        self.named_tasks = {}
        self.tasks = []
