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


from .namedobject import NamedObject


class Labels:
    def __init__(self):
        self.labeled_objects = dict()
        self.labels = []

    def add_label(self, named_object: NamedObject):
        label = named_object.create_label()
        label.set_scene_anchor(named_object.scene_anchor)
        label.check_settings()
        self.labels.append(label)
        self.labeled_objects[named_object] = label

    def remove_label(self, named_object: NamedObject):
        try:
            label = self.labeled_objects[named_object]
            del self.labeled_objects[named_object]
            self.labels.remove(label)
            named_object.remove_label()
        except KeyError:
            pass

    def check_settings(self):
        for label in self.labels:
            label.check_settings()

    def update_obs(self, observer):
        for label in self.labels:
            label.update_obs(observer)

    def check_visibility(self, frustum, pixel_size):
        for label in self.labels:
            label.check_visibility(frustum, pixel_size)

    def check_and_create_instance(self, scene_manager, camera_pos, camera_rot):
        for label in self.labels:
            label.check_and_create_instance(scene_manager, camera_pos, camera_rot)

    def check_and_update_instance(self, scene_manager, camera_pos, camera_rot):
        for label in self.labels:
            label.check_and_update_instance(scene_manager, camera_pos, camera_rot)
