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

from math import pi
from typing import TYPE_CHECKING

from direct.showbase.ShowBaseGlobal import globalClock

from ..astro import units
from .interactive import InteractiveNavigationController

if TYPE_CHECKING:
    from direct.showbase import DirectObject


class ControlNav(InteractiveNavigationController):
    """Direct body-control navigation controller.

    Drives a scene entity (e.g. a vehicle or character) through the world by
    delegating to the entity's movement controller:

    * **Up / Down** — move forward / backward.
    * **Left / Right** — rotate the body left / right.
    * **Home / End** (or mouse-wheel) — altitude change (no-op by default, but
      subclasses or external logic can override :meth:`change_altitude`).
    * **a** (hold) — fast movement (10× base speed).

    Requires a movement controller to be set via :meth:`set_controller`.
    """

    #: Rotation rate in radians per second.
    rot_step_per_sec = pi / 4
    #: Base movement speed in kilometres.
    speed = 10 * units.m
    #: Rate of altitude change per tick (unused by the default implementation).
    distance_speed = 2.0

    def __init__(self) -> None:
        InteractiveNavigationController.__init__(self)
        self.speed_factor = 1.0

    def get_name(self) -> str:
        """Return the human-readable name for this navigation mode.

        Returns:
            Display name string.
        """
        return 'Control body'

    def get_id(self) -> str:
        """Return the stable identifier for this navigation mode.

        Returns:
            Short ASCII identifier string.
        """
        return 'control'

    def require_controller(self) -> bool:
        """This controller requires a movement controller.

        Returns:
            True.
        """
        return True

    def register_events(self, event_ctrl: DirectObject) -> None:
        """Register all keyboard and mouse events for body-control navigation."""
        self.key_map = {
            "left": 0,
            "right": 0,
            "up": 0,
            "down": 0,
            "home": 0,
            "end": 0,
        }
        event_ctrl.accept("arrow_up", self.set_key, ['up', 1])
        event_ctrl.accept("arrow_up-up", self.set_key, ['up', 0])
        event_ctrl.accept("arrow_down", self.set_key, ['down', 1])
        event_ctrl.accept("arrow_down-up", self.set_key, ['down', 0])
        event_ctrl.accept("arrow_left", self.set_key, ['left', 1])
        event_ctrl.accept("arrow_left-up", self.set_key, ['left', 0])
        event_ctrl.accept("arrow_right", self.set_key, ['right', 1])
        event_ctrl.accept("arrow_right-up", self.set_key, ['right', 0])
        event_ctrl.accept("home", self.set_key, ['home', 1])
        event_ctrl.accept("home-up", self.set_key, ['home', 0])
        event_ctrl.accept("end", self.set_key, ['end', 1])
        event_ctrl.accept("end-up", self.set_key, ['end', 0])

        self.register_wheel_events(event_ctrl)

        event_ctrl.accept("a", self.fast)
        event_ctrl.accept("a-up", self.slow)

    def remove_events(self, event_ctrl: DirectObject) -> None:
        """Unregister all events registered by register_events."""
        event_ctrl.ignore("arrow_up")
        event_ctrl.ignore("arrow_up-up")
        event_ctrl.ignore("arrow_down")
        event_ctrl.ignore("arrow_down-up")
        event_ctrl.ignore("arrow_left")
        event_ctrl.ignore("arrow_left-up")
        event_ctrl.ignore("arrow_right")
        event_ctrl.ignore("arrow_right-up")
        event_ctrl.ignore("home")
        event_ctrl.ignore("home-up")
        event_ctrl.ignore("end")
        event_ctrl.ignore("end-up")

        self.remove_wheel_events(event_ctrl)

        event_ctrl.ignore("a")
        event_ctrl.ignore("a-up")

    def fast(self) -> None:
        """Engage fast movement (10× base speed)."""
        self.speed_factor = 10.0

    def slow(self) -> None:
        """Return to normal movement speed."""
        self.speed_factor = 1.0

    def update(self, time: float, dt: float) -> None:
        """Advance body-control state by one tick.

        Forwards movement and rotation commands to the underlying movement
        controller and updates the controller's animation state accordingly.

        Args:
            time: Current simulation time (seconds, unused here).
            dt: Elapsed time since the previous tick (seconds).
        """
        is_moving = False
        if self.key_map['up']:
            self.step(self.speed * self.speed_factor * dt)
            is_moving = True

        if self.key_map['down']:
            self.step(-self.speed * self.speed_factor * dt)
            is_moving = True

        if self.key_map['left']:
            self.turn(self.rot_step_per_sec * dt)

        if self.key_map['right']:
            self.turn(-self.rot_step_per_sec * dt)

        if self.key_map['home']:
            self.change_altitude(self.distance_speed * dt)

        if self.key_map['end']:
            self.change_altitude(-self.distance_speed * dt)

        if self.wheel_event_time + self.wheel_event_duration > globalClock.get_real_time():
            distance = self.wheel_direction
            self.change_altitude(distance * self.distance_speed * dt)

        if is_moving:
            self.controller.set_state('moving')
        else:
            self.controller.set_state('idle')

    def step(self, distance: float) -> None:
        """Move the controlled body forward or backward by *distance* km.

        Args:
            distance: Signed distance (positive = forward).
        """
        self.controller.step_relative(distance)

    def change_altitude(self, rate: float) -> None:
        """Altitude adjustment hook (no-op in this controller).

        ControlNav does not implement altitude adjustment directly —
        the controlled entity handles vertical movement through its own physics.
        This method exists to satisfy the interface contract shared by other
        interactive controllers. Override in a subclass if altitude control is
        required.

        Args:
            rate: Requested altitude change rate (ignored).
        """

    def turn(self, angle: float) -> None:
        """Rotate the controlled body by *angle* radians around its up axis.

        Args:
            angle: Rotation amount in radians (positive = left).
        """
        self.controller.turn_relative(angle)
