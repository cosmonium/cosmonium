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
            self.mover = SurfaceBodyMover(self.body)
        else:
            self.mover = DefaultBodyMover(self.body)

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
        #TODO: Should create dynamicOrbit and DynamicRotation instead
        self.body.orbit.dynamic = True
        self.body.rotation.dynamic = True

class DefaultBodyMover():
    def set_pos(self, position):
        self.body.orbit.position = position

    def get_pos(self):
        return self.body.orbit.position

    def get_rot(self):
        #TODO: It's not really a reference axis...
        return self.body.rotation.reference_axis.rotation

    def set_rot(self, rotation):
        self.body.rotation.reference_axis.rotation = rotation

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
        rotation = self.get_rotation()
        delta = LQuaterniond()
        delta.setFromAxisAngleRad(step, LVector3d.up())
        new_rotation = delta * rotation
        self.set_rot(new_rotation)

class SurfaceBodyMover(BodyMover):
    #We assume the frame is shared between the orbit and the rotation

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

    def get_rotation(self):
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
        new_position = frame.get_center_parent_frame() + delta
        new_position = self.body.frame_cartesian_to_spherical(new_position)
        frame.long = new_position[0]
        frame.lat = new_position[1]

    def step(self, direction, distance):
        frame = self.body.orbit.frame
        rotation = LQuaterniond()
        look_at(rotation, direction, LVector3d.up())
        rotation = rotation * frame.get_orientation_parent_frame()
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
        rotation = self.get_rotation()
        delta = LQuaterniond()
        delta.setFromAxisAngleRad(step, LVector3d.up())
        new_rotation = delta * rotation
        self.set_rot(new_rotation)

    def step_altitude(self, step):
        self.set_altitude(self.get_altitude() + step)
