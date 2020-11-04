#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2020 Laurent Deru.
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

from panda3d.core import LVector3d, LPoint3d, LQuaterniond, look_at
from cosmonium.astro.orbits import FixedOrbit, FixedPosition
from cosmonium.astro.rotations import FixedRotation
from cosmonium.astro.frame import SurfaceReferenceFrame

class BodyController():
    context = None
    def __init__(self, body):
        self.body = body
        self.mover = None

    def create_mover(self):
        if not isinstance(self.body.orbit, (FixedOrbit, FixedPosition)):
            print("Can not create a mover with dynamic orbit", self.body.orbit)
            return
        if not isinstance(self.body.rotation, FixedRotation):
            print("Can not create a mover with dynamic rotation", self.body.rotation)
            return
        if isinstance(self.body.orbit.frame, SurfaceReferenceFrame) and isinstance(self.body.rotation.frame, SurfaceReferenceFrame):
            self.mover = SurfaceBodyMover(self.body)
        else:
            self.mover = CartesianBodyMover(self.body)

    def init(self):
        self.create_mover()

    def should_update(self, time, dt):
        return self.body.visible

    def update(self, time, dt):
        pass

    def update_obs(self, observer):
        pass

    def check_visibility(self, pixel_size):
        pass

    def check_and_update_instance(self, camera_pos, camera_rot, pointset):
        pass

class BodyMover():
    def __init__(self, body):
        self.body = body

    def activate(self):
        pass

    def update(self):
        pass

    def set_pos(self, position):
        pass

    def get_pos(self):
        pass

    def get_rot(self):
        pass

    def set_rot(self, rotation):
        pass

    def delta(self, delta):
        pass

    def step(self, direction, distance):
        pass

    def step_relative(self, distance):
        pass

    def turn(self, angle):
        pass

    def turn_relative(self, step):
        pass

    def set_state(self, new_state):
        self.body.set_state(new_state)

class CartesianBodyMover(BodyMover):
    def set_pos(self, position):
        self.body.set_frame_pos(position)

    def get_pos(self):
        return self.body.get_frame_pos()

    def get_rot(self):
        return self.body.get_frame_rot()

    def set_rot(self, rotation):
        self.body.set_frame_rot(rotation)

    def delta(self, delta):
        self.set_pos(self.get_pos() + delta)

    def step(self, direction, distance):
        rotation = LQuaterniond()
        look_at(rotation, direction, LVector3d.up())
        delta = rotation.xform(LVector3d(0, distance, 0))
        self.delta(delta)

    def step_relative(self, distance):
        rotation = self.body.rotation.get_frame_rotation_at(0) #TODO: retrieve simulation time
        direction = rotation.xform(LVector3d.forward())
        self.step(direction, distance)

    def turn(self, angle):
        new_rotation = LQuaterniond()
        new_rotation.setFromAxisAngleRad(angle, LVector3d.up())
        self.set_rot(new_rotation)

    def turn_relative(self, step):
        rotation = self.get_rot()
        delta = LQuaterniond()
        delta.setFromAxisAngleRad(step, LVector3d.up())
        new_rotation = delta * rotation
        self.set_rot(new_rotation)

class SurfaceBodyMover(CartesianBodyMover):
    def __init__(self, body):
        CartesianBodyMover.__init__(self, body)
        #TODO: Should create dynamicOrbit and DynamicRotation instead
        self.body.orbit.dynamic = True
        self.body.rotation.dynamic = True
        #TODO: We assume the frame is shared between the orbit and the rotation
        #This will be simplified when the orbit and rotation will disappear for anchors
        self.frame = self.body.orbit.frame
        self.altitude = 0.0

    def update(self):
        #Refresh altitude in case the body has changed shape (often due to change of LOD)
        self.set_altitude(self.altitude)

    def set_pos(self, position):
        (x, y, altitude) = position
        new_orbit_pos = LPoint3d(x, y, 1.0)
        self.body.orbit.position = new_orbit_pos
        new_pos = self.body.orbit.get_position_at(0)
        distance = self.frame.body.get_height_under(new_pos) - self.frame.body.get_apparent_radius()
        new_orbit_pos[2] = distance + altitude
        self.altitude = altitude

    def get_pos(self):
        position = LPoint3d(self.body.orbit.position)
        position[2] = self.altitude
        return position

    def get_rot(self):
        #TODO: It's not really a reference axis...
        return self.body.rotation.reference_axis.rotation

    def set_rot(self, rotation):
        self.body.rotation.reference_axis.rotation = rotation

    def get_altitude(self):
        return self.altitude

    def set_altitude(self, altitude):
        pos = self.body.orbit.get_position_at(0)
        distance = self.body.frame.body.get_height_under(pos) - self.frame.body.get_apparent_radius()
        frame_pos = self.body.orbit.position
        frame_pos[2] = distance + altitude
        self.altitude = altitude

    def step_altitude(self, step):
        self.set_altitude(self.get_altitude() + step)

class CartesianSurfaceBodyMover(CartesianBodyMover):
    def __init__(self, body):
        CartesianBodyMover.__init__(self, body)
        self.altitude = 0.0

    def update(self):
        #Refresh altitude in case the body has changed shape (often due to change of LOD)
        self.set_altitude(self.altitude)

    def set_pos(self, position):
        (x, y, altitude) = position
        new_frame_pos = LPoint3d(x, y, 0)
        self.body.set_frame_pos(new_frame_pos)
        new_pos = self.body.get_pos()
        distance = self.body.frame.body.get_height_under(new_pos)
        new_frame_pos[2] = distance + altitude
        self.body.set_frame_pos(new_frame_pos)
        self.altitude = altitude

    def get_pos(self):
        pos = self.body.get_frame_pos()
        pos = LPoint3d(pos[0], pos[1], self.altitude)
        return pos

    def get_altitude(self):
        return self.altitude

    def set_altitude(self, altitude):
        pos = self.body.get_pos()
        distance = self.body.frame.body.get_height_under(pos)
        new_frame_pos = LPoint3d(self.body.get_frame_pos())
        new_frame_pos[2] = distance + altitude
        self.body.set_frame_pos(new_frame_pos)
        self.altitude = altitude

    #TODO: Needed to replace as the CartesianBodyMover version uses body orbit orientation
    def step_relative(self, distance):
        rotation = self.body._frame_rotation
        direction = rotation.xform(LVector3d.forward())
        self.step(direction, distance)

    def step_altitude(self, step):
        self.set_altitude(self.get_altitude() + step)
