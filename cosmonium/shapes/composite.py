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

from ..foundation import VisibleObject


class CompositeShapeObject(VisibleObject):

    def __init__(self, name):
        VisibleObject.__init__(self, name)
        self.components = []
        self.owner = None
        self.task = None

    def add_component(self, component):
        self.components.append(component)
        component.set_parent(self.parent)
        component.set_owner(self.owner)

    def set_parent(self, parent):
        VisibleObject.set_parent(self, parent)
        for component in self.components:
            component.set_parent(self.parent)

    def set_owner(self, owner):
        self.owner = owner
        for component in self.components:
            component.set_owner(self.owner)

    def check_settings(self):
        for component in self.components:
            component.check_settings()

    def add_source(self, source):
        for component in self.components:
            component.add_source(source)

    def add_after_effect(self, after_effect):
        for component in self.components:
            component.add_after_effect(after_effect)

    def task_done(self, task):
        self.task = None

    def create_instance(self):
        if not self.task:
            self.task = taskMgr.add(
                self.create_instance_task(self.owner.scene_anchor),
                sort=taskMgr.getCurrentTask().sort + 1,
                uponDeath=self.task_done,
            )

    async def create_instance_task(self, scene_anchor):
        tasks = []
        for component in self.components:
            tasks.append(component.create_instance(scene_anchor))
        await gather(*tasks)
        # TODO: Needed for VisibleObject methods
        self.instance = scene_anchor.instance.attach_new_node("dummy")
        self.instance_ready = True

    def update_lod(self, camera_pos, camera_rot):
        for component in self.components:
            component.update_lod(camera_pos, camera_rot)

    def update_instance(self, scene_manager, camera_pos, camera_rot):
        for component in self.components:
            component.update_instance(scene_manager, camera_pos, camera_rot)

    def update_shader(self):
        for component in self.components:
            component.update_shader()

    def remove_instance(self):
        for component in self.components:
            component.remove_instance()
