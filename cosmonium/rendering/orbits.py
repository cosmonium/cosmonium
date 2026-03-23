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
    def __init__(self):
        self.orbiting_objects = dict()

    def add_orbit(self, stellar_object):
        if (
            stellar_object not in self.orbiting_objects
            and stellar_object.anchor.has_orbit()
            and stellar_object.anchor.orbit.is_dynamic()
        ):
            orbit_object = Orbit(stellar_object)
            orbit_object.check_settings()
            self.orbiting_objects[stellar_object] = orbit_object

    def remove_orbit(self, stellar_object):
        if stellar_object not in self.orbiting_objects:
            return
        orbit_object = self.orbiting_objects.pop(stellar_object)
        orbit_object.remove_instance()

    def set_selected(self, stellar_object, selected):
        if not stellar_object.anchor.has_system():
            orbit_object = self.orbiting_objects.get(stellar_object)
            if orbit_object is not None:
                orbit_object.set_selected(selected)
        else:
            self.set_selected(stellar_object.anchor.system.body, selected)

    def add_system_orbits(self, system):
        for child in system.children:
            self.add_orbit(child)

    def remove_system_orbits(self, system):
        for child in system.children:
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
