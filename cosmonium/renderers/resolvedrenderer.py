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

from ..systems import StellarSystem

class ResolvedRenderer(object):
    def __init__(self, context):
        self.context = context
        self.bodies = []
        self.old_bodies = []

    def reset(self):
        self.old_bodies = self.bodies
        self.bodies = []

    def render(self, observer):
        self.print_bodies()
        camera_pos = observer.get_camera_pos()
        orientation = observer.get_camera_rot()
        for body in self.bodies:
            if isinstance(body, StellarSystem):
                body.check_and_update_instance_children(camera_pos, orientation)
            else:
                body.check_and_update_instance(camera_pos, orientation)
        for body in self.old_bodies:
            if body not in self.bodies:
                body.remove_instance()
  
    def add_body(self, body):
        self.bodies.append(body)

    def print_bodies(self):
        if self.old_bodies != self.bodies:
            print("Visible bodies", len(self.bodies), ':', ', '.join(map(lambda x: x.get_name(), self.bodies)))
