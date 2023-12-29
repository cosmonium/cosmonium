#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2023 Laurent Deru.
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


from math import pi
from panda3d.core import LVector3d, LPoint3d, LQuaterniond, look_at, LPoint3

from ..astro.orbits import FixedPosition
from ..astro.rotations import FixedRotation
from .. import utils


class BodyController():
    """
    Base class to control an existing anchor in Cosmonium.
    """
    context = None
    def __init__(self, anchor):
        self.anchor = anchor
        self.mover = None

    def create_mover(self):
        """
        Create a mover helper according to the anchor orbit, rotation and reference frame.
        Currently a mover will only be created if the anchor has a fixed orbit and rotation, which allows the mover
        to simply update them.
        If the reference frame is linked to the surface of an object, a surface mover will be created,
        otherwise a generic cartesian mover will be createDd
        """
        if not isinstance(self.anchor.orbit, FixedPosition):
            print("Can not create a mover with dynamic orbit", self.anchor.orbit)
            return
        if not isinstance(self.anchor.rotation, FixedRotation):
            print("Can not create a mover with dynamic rotation", self.anchor.rotation)
            return
        if isinstance(self.anchor.orbit.frame, SurfaceReferenceFrame) and isinstance(self.anchor.rotation.frame, SurfaceReferenceFrame):
            self.mover = SurfaceBodyMover(self.anchor)
        else:
            self.mover = CartesianBodyMover(self.anchor)

    def init(self):
        """
        Actual init() method called when the whole universe has been loaded and the anchor is ready to be controlled.
        The default inmplementation will create a mover helper to control the position and rotation of the anchor.
        """
        self.create_mover()

    def should_update(self, time, dt):
        """
        Return True if the update method should be called this cycle.
        The default implementation returns True only if the anchor is visible.
        """
        return self.anchor.visible

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
        The actual update_obs() method of the anchor will be called before this method
        :param observer: The current observer (camera)
        """
        pass

    def check_visibility(self, frustum, pixel_size):
        """
        Method called each cycle to alter the visibility property of the object.
        The actual check_visibility() method of the anchor will be called before this method
        :param frustum: Frustum of the current camera
        :param pixel_size: The size factor of a pixel on the screen.
        """
        pass

    def check_and_update_instance(self, camera_pos, camera_rot):
        """
        Method called each cycle, if the anchor is resolved, to alter the instance of the object in the scene
        The actual check_and_update_instance() method of the anchor will be called before this method
        :param camera_pos: Absolute position of the camera
        :param camera_rot: Absolute rotation of the camera.
        """
        pass


class SurfaceBodyController(BodyController):
    def __init__(self, anchor, body, long, lat):
        BodyController.__init__(self, anchor)
        self.body = body
        self.long = long
        self.lat = lat

    def create_mover(self):
        """
        """
        self.mover = CartesianBodyMover(self.anchor)
        self.update(0, 0)

    def calc_surface_position(self):
        p = self.body.surface.geodetic_to_cartesian(self.long, self.lat, 0)
        height = self.body.surface.get_alt_under(p)
        position = p + p.normalized() * height
        return position

    def calc_surface_orientation(self):
        p = self.body.surface.geodetic_to_cartesian(self.long, self.lat, 0)
        (tangent, binormal, normal) = self.body.surface.get_tangent_plane_under(p)
        rotation = LQuaterniond()
        look_at(rotation, binormal, normal)
        return rotation

    def update(self, time, dt):
        position = self.calc_surface_position()
        self.mover.set_frame_position(position)
        orientation = self.calc_surface_orientation()
        self.mover.set_frame_orientation(orientation)


class FlatSurfaceBodyController(BodyController):
    def __init__(self, anchor, position):
        BodyController.__init__(self, anchor)
        self.position = position
        self.terrain = None

    def init(self):
        self.terrain = self.anchor.body.get_terrain()
        super().init()

    def create_mover(self):
        """
        """
        self.mover = FlatSurfaceBodyMover(self.anchor, self.terrain)
        self.mover.update()

    def update(self, time, dt):
        self.mover.update()


class BodyMover():
    """
    Base class for the mover helper. A mover hides to the controller how to update the position and rotation of the anchor.
    It also provides helper method to do basic movements.
    """

    kinetic_mover = False
    position_mover = True

    def __init__(self, anchor):
        self.anchor = anchor

    def activate(self):
        pass

    def update(self):
        pass

    def feedback(self):
        pass

    def set_pos(self, position):
        """
        Set the position of the anchor in the orbit reference frame.
        :param position: The new position
        """
        pass

    def get_pos(self):
        """
        Return the position of the anchor in the orbit reference frame.
        :returns: The current position of the anchor
        """
        pass

    def set_rot(self, rotation):
        """
        Set the rotation of the anchor in the rotation reference frame.
        :param rotation: The new rotation as a Quaternion
        """
        pass

    def get_rot(self):
        """
        Return the rotation of the anchor in the rotation reference frame.
        :returns: The current rotation as a Quaternion
        """
        pass

    def delta(self, delta):
        """
        Add delta to the position of the anchor in the orbit reference frame.
        :param delta: The position offset as a Vector
        """
        pass

    def step(self, direction, distance):
        """
        Move the anchor with the given direction and distance in the orbit reference frame.
        :param direction: The direction of the movement.
        :param distance: The amplitude of the step.
        """
        pass

    def step_relative(self, distance):
        """
        Move the anchor with the given distance in the forward direction of the rotation reference frame, in the orbit reference frame.
        :param distance: The amplitude of the step.
        """
        pass

    def turn(self, angle):
        """
        Set the anchor rotation around it's vertical axis in the rotation reference frame.
        :param angle: The new rotation angle in Radians.
        """
        pass

    def turn_relative(self, step):
        """
        Turn the anchor around it's vertical axis in the rotation reference frame.
        :param step: The rotation step in Radians.
        """
        pass

    def set_state(self, new_state):
        self.anchor.body.set_state(new_state)

#Temporary class until a common interface between object and stellar bodies is implemented

class CartesianBodyMover(BodyMover):
    #TODO: Temporary
    @property
    def orbit_rot_camera(self):
        return self.anchor.body.orbit_rot_camera

    def get_absolute_reference_point(self):
        return self.anchor.get_absolute_reference_point()

    def set_frame_position(self, position):
        self.anchor.set_frame_position(position)

    def set_local_position(self, position):
        self.anchor.set_local_position(position)

    def get_frame_position(self):
        return self.anchor.get_frame_position()

    def get_local_position(self):
        return self.anchor.get_local_position()

    def set_frame_orientation(self, rotation):
        self.anchor.set_frame_orientation(rotation)

    def set_absolute_orientation(self, rotation):
        self.anchor.set_absolute_orientation(rotation)

    def get_frame_orientation(self):
        return self.anchor.get_frame_orientation()

    def get_absolute_orientation(self):
        return self.anchor.get_absolute_orientation()

    def delta(self, delta):
        self.anchor.set_frame_position(self.anchor.get_frame_position() + delta)

    def delta_local(self, delta):
        self.set_local_position(self.get_local_position() + delta)

    def step(self, direction, distance):
        self.delta(direction * distance)

    def step_relative(self, distance):
        rotation = self.anchor.get_frame_orientation()
        direction = rotation.xform(LVector3d.forward())
        self.delta(direction * distance)

    def turn_angle(self, angle):
        new_rotation = LQuaterniond()
        new_rotation.set_from_axis_angle_rad(angle, LVector3d.up())
        self.anchor.set_frame_orientation(new_rotation)

    def turn(self, orientation):
        self.anchor.set_frame_orientation(orientation)

    def turn_local(self, orientation):
        self.anchor.set_absolute_orientation(orientation)

    def step_turn(self, delta):
        self.anchor.set_frame_orientation(delta * self.anchor.get_frame_orientation())

    def step_turn_local(self, delta):
        self.anchor.set_absolute_orientation(delta * self.anchor.get_absolute_orientation())

    def turn_relative(self, step):
        rotation = self.anchor.get_frame_orientation()
        delta = LQuaterniond()
        delta.set_from_axis_angle_rad(step, LVector3d.up())
        new_rotation = delta * rotation
        self.anchor.set_frame_orientation(new_rotation)

    def turn_back(self):
        new_rot = utils.relative_rotation(self.anchor.get_absolute_orientation(), LVector3d.up(), pi)
        self.anchor.set_absolute_orientation(new_rot)

class SurfaceBodyMover(CartesianBodyMover):
    def __init__(self, anchor):
        CartesianBodyMover.__init__(self, anchor)
        self.surface = surface
        self.altitude = 0.0

    def update(self):
        #Refresh altitude in case the anchor has changed shape (often due to change of LOD)
        self.set_altitude(self.altitude)
        # Force internal update of the controlled anchor
        self.anchor.update(0, 0)

    def set_pos(self, position):
        (x, y, altitude) = position
        new_frame_pos = LPoint3d(x, y, 1.0)
        new_local_pos = self.anchor.calc_local_position_of_frame(new_frame_pos)
        distance = self.surface.get_height_under(new_local_pos)
        new_frame_pos[2] = distance + altitude
        self.anchor.set_frame_position(new_frame_pos)
        self.altitude = altitude

    def get_pos(self):
        return self.anchor.get_frame_position()

    def get_rot(self):
        return self.anchor.get_frame_orientation()

    def set_rot(self, rotation):
        self.anchor.set_frame_orientation(rotation)

    def get_altitude(self):
        return self.altitude

    def set_altitude(self, altitude):
        pos = self.anchor.get_local_position()
        distance = self.surface.get_height_under(pos)
        new_frame_pos = LPoint3d(self.anchor.get_frame_position())
        new_frame_pos[2] = distance + altitude
        self.anchor.set_frame_position(new_frame_pos)
        self.altitude = altitude

    def step_altitude(self, step):
        self.set_altitude(self.get_altitude() + step)

class FlatSurfaceBodyMover(CartesianBodyMover):
    def __init__(self, anchor, surface):
        CartesianBodyMover.__init__(self, anchor)
        self.surface = surface
        self.altitude = 0.0

    def update(self):
        #Refresh altitude in case the anchor has changed shape (often due to change of LOD)
        self.set_altitude(self.altitude)
        # Force internal update of the controlled anchor
        self.anchor.update(0, 0)

    def set_local_position(self, position):
        (x, y, z) = position
        new_frame_pos = LPoint3d(x, y, 0)
        self.anchor.set_frame_position(new_frame_pos)
        new_pos = self.anchor.get_local_position()
        distance = self.surface.get_height_under(new_pos)
        new_frame_pos[2] = distance + self.altitude
        self.anchor.set_frame_position(new_frame_pos)

    def get_position(self):
        pos = self.anchor.get_frame_position()
        pos = LPoint3d(pos[0], pos[1], self.altitude)
        return pos

    def get_altitude(self):
        return self.altitude

    def set_altitude(self, altitude):
        pos = self.anchor.get_local_position()
        distance = self.surface.get_height_under(pos)
        new_frame_pos = LPoint3d(self.anchor.get_frame_position())
        new_frame_pos[2] = distance + altitude
        self.anchor.set_frame_position(new_frame_pos)
        self.altitude = altitude

    def step_altitude(self, step):
        self.set_altitude(self.get_altitude() + step)
