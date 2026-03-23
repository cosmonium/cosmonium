#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2025 Laurent Deru.
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


from ..astro.orbits import FixedPosition
from ..components.annotations.body_label import FixedOrbitLabel, StellarBodyLabel


class Labels:
    def __init__(self):
        self.labeled_objects = dict()
        self.labels = []

    def add_label(self, named_object):
        if not named_object.anchor.has_orbit() or isinstance(named_object.anchor.orbit, FixedPosition):
            label = FixedOrbitLabel(named_object.get_ascii_name() + '-label', named_object)
        else:
            label = StellarBodyLabel(named_object.get_ascii_name() + '-label', named_object)
        label.set_scene_anchor(named_object.scene_anchor)
        label.check_settings()
        self.labels.append(label)
        self.labeled_objects[named_object] = label

    def remove_label(self, named_object):
        try:
            label = self.labeled_objects[named_object]
            del self.labeled_objects[named_object]
            self.labels.remove(label)
            label.remove_instance()
        except KeyError:
            pass

    def get_label(self, named_object):
        return self.labeled_objects.get(named_object)

    def show_label(self, named_object):
        label = self.labeled_objects.get(named_object)
        if label is not None:
            label.show()

    def hide_label(self, named_object):
        label = self.labeled_objects.get(named_object)
        if label is not None:
            label.hide()

    def toggle_label(self, named_object):
        label = self.labeled_objects.get(named_object)
        if label is not None:
            label.toggle_shown()

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
