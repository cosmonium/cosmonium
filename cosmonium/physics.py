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

from panda3d.core import LVector3d
from panda3d.bullet import BulletWorld, BulletDebugNode

class Physics():
    def __init__(self, enable_debug):
        self.enable_debug = enable_debug
        self.physics_world = None
        self.render_world = None
        self.debug = None

    def enable(self):
        self.physics_world = BulletWorld()
        self.render_world = render.attach_new_node('physics-root')
        if self.enable_debug:
            self.debug = self.render_world.attach_new_node(BulletDebugNode('Debug'))
            self.debug.show()
            #self.debug.node().showNormals(True)
            self.physics_world.set_debug_node(self.debug.node())

    def set_gravity(self, gravity):
        self.physics_world.set_gravity(*LVector3d(0, 0, -gravity))

    def disable(self):
        self.physics_world = None
        self.render_world.remove_node()
        self.render_world = None
        if self.debug is not None:
            self.debug.remove_node()
            self.debug = None

    def add(self, instance):
        self.physics_world.attach_rigid_body(instance.node())
        instance.reparent_to(self.render_world)

    def remove(self, instance):
        self.physics_world.remove_rigid_body(instance.node())

    def update(self, time, dt):
        if self.physics_world is None: return
        self.physics_world.do_physics(dt)
