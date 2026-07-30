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


from math import pi

from panda3d.core import LPoint3d, LQuaterniond, LVector3d, look_at

from ..mathutil.quaternion import relative_rotation
from .base import MovementController


class PositionMovementController(MovementController):
    """
    Controller for object movement operations based on position.
    """

    position_mover = True

    # Position/Rotation Interface
    def set_local_position(self, position):
        """
        Sets the position in the local reference frame.

        Args:
            position: Position vector in local coordinates.
        """
        pass

    def get_local_position(self):
        """
        Gets the position in the local reference frame.

        Returns:
            The position vector in local coordinates.
        """
        pass

    def set_frame_position(self, position):
        """
        Sets the position in the object reference frame.

        Args:
            position: Position vector in object reference frame.
        """
        pass

    def get_frame_position(self):
        """
        Gets the position in the object reference frame.

        Returns:
            The position vector in object reference frame.
        """
        pass

    def set_frame_orientation(self, rotation):
        """
        Sets the orientation in the object reference frame.

        Args:
            rotation: Orientation (rotation) in object reference frame.
        """
        pass

    def get_frame_orientation(self):
        """
        Gets the orientation in the object reference frame.

        Returns:
            The orientation (rotation) in object reference frame.
        """
        pass

    def set_absolute_orientation(self, rotation):
        """
        Sets the absolute orientation.

        Args:
            rotation: Absolute orientation (rotation).
        """
        pass

    def get_absolute_orientation(self):
        """
        Gets the absolute orientation.

        Returns:
            The absolute orientation (rotation).
        """
        pass

    # Movement Interface
    def delta(self, delta):
        """
        Adds a delta to the position in the object reference frame.

        Args:
            delta: Delta vector in object reference frame.
        """
        pass

    def delta_local(self, delta):
        """
        Adds a delta to the local position in the local reference frame.

        Args:
            delta: Delta vector in local reference frame.
        """
        pass

    def step(self, direction, distance):
        """
        Moves in the given direction by the specified distance in the local reference frame.

        Args:
            direction: Direction vector in local reference frame.
            distance: Distance to move.
        """
        pass

    def step_relative(self, distance):
        """
        Move forward in object reference frame.

        Args:
            distance: Distance to move.
        """
        pass

    def turn(self, orientation):
        """
        Set orientation in object reference frame.

        Args:
            orientation: Orientation (rotation) in object reference frame.
        """
        pass

    def turn_angle(self, angle):
        """
        Set rotation around vertical axis in object reference frame.

        Args:
            angle: Rotation angle in radians.
        """
        pass

    def turn_local(self, orientation):
        """
        Set orientation in local reference frame.

        Args:
            orientation: Orientation (rotation) in local reference frame.
        """
        pass

    def step_turn(self, delta):
        """
        Apply rotation delta in object reference frame.

        Args:
            delta: Rotation delta in object reference frame.
        """
        pass

    def step_turn_local(self, delta):
        """
        Apply rotation delta  local reference frame.

        Args:
            delta: Rotation delta in local reference frame.
        """
        pass

    def turn_relative(self, step):
        """
        Turn around vertical axis.

        Args:
            step: Rotation angle in radians.
        """
        pass

    def turn_back(self):
        """Turn 180 degrees"""
        pass

    def get_absolute_reference_point(self):
        """
        Get absolute reference point for anchor.

        Returns:
            Absolute reference point in world coordinates.
        """
        return self.anchor.get_absolute_reference_point()


class CartesianMovementController(PositionMovementController):
    """Movement controller for general 3D cartesian space"""

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
        new_rot = relative_rotation(self.anchor.get_absolute_orientation(), LVector3d.up(), pi)
        self.anchor.set_absolute_orientation(new_rot)


class SurfaceMovementController(PositionMovementController):
    """
    Movement controller for objects on curved surfaces.
    Note: The implementation is broken.
    """

    def __init__(self, anchor, body, longitude, latitude, altitude):
        super().__init__(anchor)
        self.body = body
        self.longitude = longitude
        self.latitude = latitude
        self.altitude = altitude

    def init(self):
        """Initialize and set initial position"""
        super().init()
        self.update(0, 0)

    def calc_surface_position(self):
        """Calculate position on surface"""
        p = self.body.surface.model.geodetic_to_cartesian(self.longitude, self.latitude, 0)
        height = self.body.surface.get_alt_under(p) + self.altitude
        position = p + p.normalized() * height
        return position

    def calc_surface_orientation(self):
        """Calculate orientation aligned to surface"""
        p = self.body.surface.model.geodetic_to_cartesian(self.longitude, self.latitude, 0)
        tangent, binormal, normal = self.body.surface.get_tangent_plane_under(p)
        rotation = LQuaterniond()
        look_at(rotation, binormal, normal)
        return rotation

    def update(self, time, dt):
        """Update position and orientation"""
        position = self.calc_surface_position()
        self.set_frame_position(position)
        orientation = self.calc_surface_orientation()
        self.set_frame_orientation(orientation)

    def set_frame_position(self, position):
        x, y, altitude = position
        new_frame_pos = LPoint3d(x, y, 1.0)
        new_local_pos = self.anchor.calc_local_position_of_frame(new_frame_pos)
        distance = self.body.get_height_under(new_local_pos)
        new_frame_pos[2] = distance + altitude
        self.anchor.set_frame_position(new_frame_pos)
        self.altitude = altitude

    def get_frame_position(self):
        return self.anchor.get_frame_position()

    def set_frame_orientation(self, rotation):
        self.anchor.set_frame_orientation(rotation)

    def get_frame_orientation(self):
        return self.anchor.get_frame_orientation()

    def set_local_position(self, position):
        self.anchor.set_local_position(position)

    def get_local_position(self):
        return self.anchor.get_local_position()

    def set_absolute_orientation(self, rotation):
        self.anchor.set_absolute_orientation(rotation)

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
        new_rot = relative_rotation(self.anchor.get_absolute_orientation(), LVector3d.up(), pi)
        self.anchor.set_absolute_orientation(new_rot)

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


class FlatSurfaceMovementController(CartesianMovementController):
    """Movement controller for objects on terrain"""

    def __init__(self, anchor, terrain, position=None, altitude=0.0):
        super().__init__(anchor)
        self.terrain = terrain
        if position is None:
            position = LPoint3d(0, 0, 0)
        self.init_position = position
        self.altitude = altitude

    def init(self):
        """Initialize with terrain height"""
        super().init()
        if self.terrain is None:
            self.terrain = self.anchor.body.get_terrain()
        # TODO: Set initial position
        self.update_position()

    def update_position(self):
        """Refresh position with terrain height"""
        # Refresh altitude in case the terrain has changed shape (often due to change of LOD)
        # TODO: This is a workaround, we should instead listen to terrain changes and update position only when needed
        self.set_altitude(self.altitude)
        # Force internal update of the controlled anchor
        self.anchor.update(0, 0)

    def update(self, time, dt):
        """Update position with terrain height"""
        self.update_position()

    def set_local_position(self, position):
        x, y, z = position
        new_frame_pos = LPoint3d(x, y, 0)
        self.anchor.set_frame_position(new_frame_pos)
        new_pos = self.anchor.get_local_position()
        distance = self.terrain.get_height_under(new_pos)
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
        distance = self.terrain.get_height_under(pos)
        new_frame_pos = LPoint3d(self.anchor.get_frame_position())
        new_frame_pos[2] = distance + altitude
        self.anchor.set_frame_position(new_frame_pos)
        self.altitude = altitude

    def step_altitude(self, step):
        self.set_altitude(self.get_altitude() + step)
