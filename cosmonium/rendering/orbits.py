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


from ..components.annotations.orbit import Orbit


class Orbits:
    """Registry of the visible orbits.

    An orbit is only drawn for the children of a resolved system.
    """

    def __init__(self):
        self.orbiting_objects = dict()

    def add_orbit(self, anchor):
        if anchor not in self.orbiting_objects and anchor.has_orbit() and anchor.orbit.is_dynamic():
            orbit_object = Orbit(anchor)
            orbit_object.check_settings()
            self.orbiting_objects[anchor] = orbit_object

    def remove_orbit(self, anchor):
        if anchor not in self.orbiting_objects:
            return
        orbit_object = self.orbiting_objects.pop(anchor)
        orbit_object.remove_instance()

    def set_selected(self, anchor, selected):
        if not anchor.has_system():
            orbit_object = self.orbiting_objects.get(anchor)
            if orbit_object is not None:
                orbit_object.set_selected(selected)
        else:
            self.set_selected(anchor.system, selected)

    def add_system_orbits(self, system_anchor):
        for child in system_anchor.get_children():
            self.add_orbit(child)

    def remove_system_orbits(self, system_anchor):
        for child in system_anchor.get_children():
            self.remove_orbit(child)

    def check_settings(self):
        for orbit_object in self.orbiting_objects.values():
            orbit_object.check_settings()

    def check_visibility(self, frustum, pixel_size):
        for orbit_object in self.orbiting_objects.values():
            orbit_object.check_visibility(frustum, pixel_size)

    def check_and_create_instance(self, scene_manager, camera_pos, camera_rot):
        for orbit_object in self.orbiting_objects.values():
            orbit_object.check_and_create_instance(scene_manager, camera_pos, camera_rot)
            if orbit_object.instance is not None:
                scene_manager.add_spread_object(orbit_object.instance)

    def check_and_update_instance(self, scene_manager, camera_pos, camera_rot):
        for orbit_object in self.orbiting_objects.values():
            orbit_object.check_and_update_instance(scene_manager, camera_pos, camera_rot)
