#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2019 Laurent Deru.
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

from __future__ import print_function
from __future__ import absolute_import

class OrbitsRenderer(object):
    def __init__(self, context):
        self.context = context
        self.orbits = []
        self.old_orbits = []

    def reset(self):
        self.old_orbits = self.orbits
        self.orbits = []

    def update(self, observer):
        camera_pos = observer.get_camera_pos()
        camera_rot = observer.get_camera_rot()
        frustum = observer.rel_frustum
        pixel_size = observer.pixel_size
        for body in self.orbits:
            if body.orbit_object is None:
                body.create_orbit_object()
                body.orbit_object.check_settings()
            body.orbit_object.check_visibility(frustum, pixel_size)
            body.orbit_object.check_and_update_instance(camera_pos, camera_rot)
        for body in self.old_orbits:
            if body not in self.orbits and body.orbit_object is not None:
                body.orbit_object.remove_instance()

    def add_orbit(self, body):
        self.orbits.append(body)

