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


from __future__ import annotations

import sys
from math import pi
from typing import TYPE_CHECKING, Optional

from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import LQuaterniond, LVector3d

from .. import settings
from ..astro import units
from .interactive import InteractiveNavigationController

if TYPE_CHECKING:
    from direct.showbase import DirectObject

    from ..objects.stellarobject import StellarObject


class WalkNav(InteractiveNavigationController):
    """Surface-walk (fly) navigation controller.

    Moves an observer along the surface of a target body, following the terrain
    curvature so that the altitude above the surface is maintained.

    * **Up / Down** — move forward / backward along the surface.
    * **Left / Right** — yaw (turn) left / right.
    * **Shift + Up / Down** — pitch the camera up / down.
    * **Shift + Left / Right** — additional yaw (same as Left / Right).
    * **Ctrl + Left / Right** (or **Alt** on macOS) — roll.
    * **Home / End** (or mouse-wheel) — increase / decrease altitude.
    * **a** (hold) — activate fast movement (10x speed).

    Requires a target body to be set via :meth:`set_target`.
    """

    #: Rotation rate in radians per second.
    rot_step_per_sec = pi / 4
    #: Base movement speed in kilometres (converted from metres by :mod:`~cosmonium.astro.units`).
    speed = 10 * units.m
    #: Rate of altitude change per tick when Home/End is pressed.
    distance_speed = 2.0

    def __init__(self) -> None:
        InteractiveNavigationController.__init__(self)
        self.body: Optional[StellarObject] = None
        self.speed_factor = 1.0

    def get_name(self) -> str:
        """Return the human-readable name for this navigation mode.

        Returns:
            Display name string.
        """
        return 'Fly'

    def get_id(self) -> str:
        """Return the stable identifier for this navigation mode.

        Returns:
            Short ASCII identifier string.
        """
        return 'walk'

    def require_target(self) -> bool:
        """This controller requires a target body.

        Returns:
            True.
        """
        return True

    def set_target(self, target: StellarObject) -> None:
        """Set the surface body that the observer walks on.

        Args:
            target: Celestial body or scene object with surface geometry.
        """
        self.body = target

    def register_events(self, event_ctrl: DirectObject) -> None:
        """Register all keyboard and mouse events for surface-walk navigation."""
        self.key_map = {
            "left": 0,
            "right": 0,
            "up": 0,
            "down": 0,
            "home": 0,
            "end": 0,
            "shift-left": 0,
            "shift-right": 0,
            "shift-up": 0,
            "shift-down": 0,
            "control-left": 0,
            "control-right": 0,
        }
        event_ctrl.accept("arrow_up", self.set_key, ['up', 1])
        event_ctrl.accept("arrow_up-up", self.set_key, ['up', 0, 'shift-up'])
        event_ctrl.accept("arrow_down", self.set_key, ['down', 1])
        event_ctrl.accept("arrow_down-up", self.set_key, ['down', 0, 'shift-down'])
        event_ctrl.accept("arrow_left", self.set_key, ['left', 1])
        event_ctrl.accept("arrow_left-up", self.set_key, ['left', 0, 'shift-left', 'control-left'])
        event_ctrl.accept("arrow_right", self.set_key, ['right', 1])
        event_ctrl.accept("arrow_right-up", self.set_key, ['right', 0, 'shift-right', 'control-right'])
        event_ctrl.accept("shift-arrow_up", self.set_key, ['shift-up', 1])
        event_ctrl.accept("shift-arrow_down", self.set_key, ['shift-down', 1])
        event_ctrl.accept("shift-arrow_left", self.set_key, ['shift-left', 1])
        event_ctrl.accept("shift-arrow_right", self.set_key, ['shift-right', 1])
        if sys.platform != "darwin":
            event_ctrl.accept("control-arrow_left", self.set_key, ['control-left', 1])
            event_ctrl.accept("control-arrow_right", self.set_key, ['control-right', 1])
        else:
            event_ctrl.accept("alt-arrow_left", self.set_key, ['control-left', 1])
            event_ctrl.accept("alt-arrow_right", self.set_key, ['control-right', 1])
        event_ctrl.accept("home", self.set_key, ['home', 1])
        event_ctrl.accept("home-up", self.set_key, ['home', 0])
        event_ctrl.accept("end", self.set_key, ['end', 1])
        event_ctrl.accept("end-up", self.set_key, ['end', 0])

        self.register_wheel_events(event_ctrl)

        event_ctrl.accept("a", self.fast)
        event_ctrl.accept("a-up", self.slow)

    def remove_events(self, event_ctrl):
        """Unregister all events registered by register_events."""
        event_ctrl.ignore("arrow_up")
        event_ctrl.ignore("arrow_up-up")
        event_ctrl.ignore("arrow_down")
        event_ctrl.ignore("arrow_down-up")
        event_ctrl.ignore("arrow_left")
        event_ctrl.ignore("arrow_left-up")
        event_ctrl.ignore("arrow_right")
        event_ctrl.ignore("arrow_right-up")
        event_ctrl.ignore("shift-arrow_up")
        event_ctrl.ignore("shift-arrow_down")
        event_ctrl.ignore("shift-arrow_left")
        event_ctrl.ignore("shift-arrow_right")
        if sys.platform != "darwin":
            event_ctrl.ignore("control-arrow_left")
            event_ctrl.ignore("control-arrow_right")
        else:
            event_ctrl.ignore("alt-arrow_left")
            event_ctrl.ignore("alt-arrow_right")
        event_ctrl.ignore("home")
        event_ctrl.ignore("home-up")
        event_ctrl.ignore("end")
        event_ctrl.ignore("end-up")

        self.remove_wheel_events(event_ctrl)

        event_ctrl.ignore("a")
        event_ctrl.ignore("a-up")

    def fast(self) -> None:
        """Engage fast movement (10x base speed)."""
        self.speed_factor = 10.0

    def slow(self) -> None:
        """Return to normal movement speed."""
        self.speed_factor = 1.0

    def update(self, time: float, dt: float) -> None:
        """Advance surface-walk state by one tick.

        Handles forward/backward stepping, yaw/pitch/roll rotation, and altitude
        adjustment via Home/End or the mouse wheel.

        Args:
            time: Current simulation time (seconds, unused here).
            dt: Elapsed time since the previous tick (seconds).
        """
        if self.key_map['up']:
            self.step(self.speed * self.speed_factor * dt)

        if self.key_map['down']:
            self.step(-self.speed * self.speed_factor * dt)

        if self.key_map['left']:
            self.turn(LVector3d.up(), self.rot_step_per_sec * dt)

        if self.key_map['right']:
            self.turn(LVector3d.up(), -self.rot_step_per_sec * dt)

        if self.key_map['shift-up']:
            self.turn(LVector3d.right(), self.rot_step_per_sec * dt)

        if self.key_map['shift-down']:
            self.turn(LVector3d.right(), -self.rot_step_per_sec * dt)

        if self.key_map['shift-left']:
            self.turn(LVector3d.up(), self.rot_step_per_sec * dt)

        if self.key_map['shift-right']:
            self.turn(LVector3d.up(), -self.rot_step_per_sec * dt)

        if self.key_map['control-left']:
            self.turn(LVector3d.forward(), self.rot_step_per_sec * dt)

        if self.key_map['control-right']:
            self.turn(LVector3d.forward(), -self.rot_step_per_sec * dt)

        if self.key_map['home']:
            self.change_altitude(self.distance_speed * dt)

        if self.key_map['end']:
            self.change_altitude(-self.distance_speed * dt)

        if self.wheel_event_time + self.wheel_event_duration > globalClock.get_real_time():
            distance = self.wheel_direction
            self.change_altitude(distance * self.distance_speed * dt)

    def step(self, distance: float) -> None:
        """Move the observer along the surface by *distance* kilometres.

        The movement direction is derived from the observer's forward orientation
        projected onto the local surface tangent plane, so that the observer
        hugs the terrain regardless of the body's curvature.

        Args:
            distance: Signed distance to travel (positive = forward).
        """
        object_position = self.controller.get_local_position()
        _lon, _lat, normal = self.body.get_tangent_plane_under(object_position)
        surface_point = self.body.get_point_under(self.controller.get_local_position())
        direction = self.controller.get_local_position() - surface_point
        altitude = direction.dot(normal)
        direction = self.controller.get_absolute_orientation().xform(LVector3d.forward())
        projected = direction - normal * direction.dot(normal)
        projected.normalize()
        new_position = self.body.get_point_under(object_position + projected * distance)
        _lon, _lat, normal = self.body.get_tangent_plane_under(new_position)
        self.controller.set_local_position(new_position + normal * altitude)

    def change_altitude(self, rate: float) -> None:
        """Adjust the observer's altitude above the surface.

        If the observer would fall below the minimum safe altitude
        (settings.min_altitude) it is snapped to that value
        instead.

        Args:
            rate: Fractional altitude change; positive moves away from the
                surface, negative moves towards it.
        """
        if rate == 0.0:
            return
        tangent, binormal, normal = self.body.get_tangent_plane_under(self.controller.get_local_position())
        surface_point = self.body.get_point_under(self.controller.get_local_position())
        direction = self.controller.get_local_position() - surface_point
        altitude = direction.dot(normal)
        if altitude > 0:
            if rate < 0 or altitude >= settings.min_altitude:
                self.controller.delta_local(-normal * altitude * rate)
        else:
            self.controller.set_local_position(surface_point + settings.min_altitude * normal)

    def turn(self, axis: LVector3d, angle: float) -> None:
        """Apply an incremental rotation to the movement controller.

        Args:
            axis: Unit vector (in local frame) to rotate around.
            angle: Rotation amount in radians.
        """
        rot = LQuaterniond()
        rot.setFromAxisAngleRad(angle, axis)
        self.controller.step_turn(rot)
