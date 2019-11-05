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
    """
    Base class to control an existing body in Cosmonium.
    """
    context = None
    def __init__(self, body):
        self.body = body
        self.mover = None

    def create_mover(self):
        """
        Create a mover helper according to the body orbit, rotation and reference frame.
        Currently a mover will only be created if the body has a fixed orbit and rotation, which allows the mover
        to simply update them.
        If the reference frame is linked to the surface of an object, a surface mover will be created,
        otherwise a generic cartesian mover will be createDd
        """
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
        """
        Actual init() method called when the whole universe has been loaded and the body is ready to be controlled.
        The default inmplementation will create a mover helper to control the position and rotation of the body.
        """
        self.create_mover()

    def should_update(self, time, dt):
        """
        Return True if the update method should be called this cycle.
        The default implementation returns True only if the body is visible.
        """
        return self.body.visible

    def update(self, time, dt):
        """
        Method called each cycle to update the physical properties of the object, e.g. it's position, rotation, ...
        :param time: The time of the simulation expressed in Julian days
        :param dt: The interval since the last cycle in seconds.
        """
        pass

    def update_obs(self, observer):
        """
        Method called each cycle to alter the properties of the object related to the actual position of the observer.
        The actual update_obs() method of the body will be called before this method
        :param observer: The current observer (camera)
        """
        pass

    def check_visibility(self, frustum, pixel_size):
        """
        Method called each cycle to alter the visibility property of the object.
        The actual check_visibility() method of the body will be called before this method
        :param frustum: Frustum of the current camera
        :param pixel_size: The size factor of a pixel on the screen.
        """
        pass

    def check_and_update_instance(self, camera_pos, camera_rot):
        """
        Method called each cycle, if the body is resolved, to alter the instance of the object in the scene
        The actual check_and_update_instance() method of the body will be called before this method
        :param camera_pos: Absolute position of the camera
        :param camera_rot: Absolute rotation of the camera.
        """
        pass

class BodyMover():
    """
    Base class for the mover helper. A mover hides to the controller how to update the position and rotation of the body.
    It also provides helper method to do basic movements.
    """
    def __init__(self, body):
        self.body = body

    def activate(self):
        pass

    def update(self):
        pass

    def set_pos(self, position):
        """
        Set the position of the body in the orbit reference frame.
        :param position: The new position
        """
        pass

    def get_pos(self):
        """
        Return the position of the body in the orbit reference frame.
        :returns: The current position of the body
        """
        pass

    def set_rot(self, rotation):
        """
        Set the rotation of the body in the rotation reference frame.
        :param rotation: The new rotation as a Quaternion
        """
        pass

    def get_rot(self):
        """
        Return the rotation of the body in the rotation reference frame.
        :returns: The current rotation as a Quaternion
        """
        pass

    def delta(self, delta):
        """
        Add delta to the position of the body in the orbit reference frame.
        :param delta: The position offset as a Vector
        """
        pass

    def step(self, direction, distance):
        """
        Move the body with the given direction and distance in the orbit reference frame.
        :param direction: The direction of the movement.
        :param distance: The amplitude of the step.
        """
        pass

    def step_relative(self, distance):
        """
        Move the body with the given distance in the forward direction of the rotation reference frame, in the orbit reference frame.
        :param distance: The amplitude of the step.
        """
        pass

    def turn(self, angle):
        """
        Set the body rotation around it's vertical axis in the rotation reference frame.
        :param angle: The new rotation angle in Radians.
        """
        pass

    def turn_relative(self, step):
        """
        Turn the body around it's vertical axis in the rotation reference frame.
        :param step: The rotation step in Radians.
        """
        pass

    def set_state(self, new_state):
        self.body.set_state(new_state)

class CartesianBodyMover(BodyMover):
    def set_pos(self, position):
        self.body.orbit.set_frame_position(position)

    def get_pos(self):
        return self.body.orbit.get_frame_position_at(0)

    def set_rot(self, rotation):
        self.body.rotation.reference_axis.set_rotation(rotation)

    def get_rot(self):
        return self.body.rotation.reference_axis.get_rotation_at(0)

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
