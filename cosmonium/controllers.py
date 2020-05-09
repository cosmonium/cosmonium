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

from panda3d.core import LVector3d, LQuaterniond, look_at
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
            self.mover = SurfaceFrameBodyMover(self.body)
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

    def check_and_update_instance(self, camera_pos, orientation, pointset):
        pass

class BodyMover():
    def __init__(self, body):
        self.body = body

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
        self.body.set_pos(position)

    def get_pos(self):
        return self.body.get_pos()

    def get_rot(self):
        return self.body.get_rot()

    def set_rot(self, rotation):
        self.body.set_rot(rotation)

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

class SurfaceFrameBodyMover(CartesianBodyMover):
    #We assume the frame is shared between the orbit and the rotation
    #This will be simplified when the orbit and rotation will disappear for anchors
    def __init__(self, body):
        CartesianBodyMover.__init__(self, body)
        #TODO: Should create dynamicOrbit and DynamicRotation instead
        self.body.orbit.dynamic = True
        self.body.rotation.dynamic = True

    def set_pos(self, position):
        frame = self.body.orbit.frame
        (long, lat, alt) = position
        frame.long = long
        frame.lat = lat
        self.body.orbit.position.set_z(alt)

    def get_pos(self):
        frame = self.body.orbit.frame
        alt = self.body.orbit.position.get_z()
        return (frame.long, frame.lat, alt)

    def get_rot(self):
        #TODO: It's not really a reference axis...
        return self.body.rotation.reference_axis.rotation

    def set_rot(self, rotation):
        self.body.rotation.reference_axis.rotation = rotation

    def get_altitude(self):
        return self.body.orbit.position.get_z()

    def set_altitude(self, altitude):
        self.body.orbit.position.set_z(altitude)

    def delta(self, delta):
        frame = self.body.orbit.frame
        frame_delta = frame.get_orientation_parent_frame().xform(delta)
        new_position = frame.get_center_parent_frame() + frame_delta
        new_position = self.body.frame_cartesian_to_spherical(new_position)
        frame.long = new_position[0]
        frame.lat = new_position[1]

    def step_altitude(self, step):
        self.set_altitude(self.get_altitude() + step)

class CartesianSurfaceFrameBodyMover(CartesianBodyMover):
    def set_pos(self, position):
        frame = self.body.frame
        (x, y, alt) = position
        frame.position[0] = x
        frame.position[1] = y
        self.body._frame_position[2] = alt

    def get_pos(self):
        frame = self.body.frame
        return (frame.position[0], frame.position[1], self.body._frame_position[2])

    def get_rot(self):
        return self.body._frame_rotation

    def set_rot(self, rotation):
        self.body._frame_rotation = rotation

    def get_altitude(self):
        return self.body._frame_position[2]

    def set_altitude(self, altitude):
        self.body._frame_position[2]

    def delta(self, delta):
        frame = self.body.frame
        frame_delta = frame.get_orientation_parent_frame().xform(delta)
        new_position = frame.get_center_parent_frame() + frame_delta
        frame.position[0] = new_position[0]
        frame.position[1] = new_position[1]

    def step_relative(self, distance):
        rotation = self.body._frame_rotation
        direction = rotation.xform(LVector3d.forward())
        self.step(direction, distance)

    def step_altitude(self, step):
        self.set_altitude(self.get_altitude() + step)
