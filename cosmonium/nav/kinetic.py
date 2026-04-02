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

from panda3d.core import LVector3d

from ..astro import units
from .interactive import InteractiveNavigationController

if TYPE_CHECKING:
    from direct.showbase import DirectObject


class KineticNav(InteractiveNavigationController):
    """Physics-driven (kinetic) navigation controller.

    Sends velocity commands to a physics-based movement controller instead of
    issuing discrete step/turn calls:

    * **Up / Down** — set forward/backward velocity.
    * **Left / Right** — rotate left / right.
    * **Space** — jump (when supported by the physics controller).

    Requires a movement controller to be set via :meth:`set_controller`.
    """

    #: Rotation rate in radians per second.
    rot_step_per_sec = pi / 4
    #: Base movement speed in kilometres.
    speed = 10 * units.m
    #: Unused — kept for API consistency with other nav controllers.
    distance_speed = 2.0

    def __init__(self) -> None:
        InteractiveNavigationController.__init__(self)
        self.speed_factor = 1.0

    def get_name(self) -> str:
        """Return the human-readable name for this navigation mode.

        Returns:
            Display name string.
        """
        return 'Kinetic control'

    def get_id(self) -> str:
        """Return the stable identifier for this navigation mode.

        Returns:
            Short ASCII identifier string.
        """
        return 'kinetic'

    def require_controller(self) -> bool:
        """This controller requires a movement controller.

        Returns:
            True.
        """
        return True

    def register_events(self, event_ctrl: DirectObject) -> None:
        """Register all keyboard events for kinetic navigation."""
        self.key_map = {"left": 0, "right": 0, "up": 0, "down": 0, "home": 0, "end": 0, "jump": 0}
        event_ctrl.accept("arrow_up", self.set_key, ['up', 1])
        event_ctrl.accept("arrow_up-up", self.set_key, ['up', 0])
        event_ctrl.accept("arrow_down", self.set_key, ['down', 1])
        event_ctrl.accept("arrow_down-up", self.set_key, ['down', 0])
        event_ctrl.accept("arrow_left", self.set_key, ['left', 1])
        event_ctrl.accept("arrow_left-up", self.set_key, ['left', 0])
        event_ctrl.accept("arrow_right", self.set_key, ['right', 1])
        event_ctrl.accept("arrow_right-up", self.set_key, ['right', 0])
        event_ctrl.accept(" ", self.set_key, ['jump', 1])
        event_ctrl.accept(" -up", self.set_key, ['jump', 0])

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
        event_ctrl.ignore(" ")
        event_ctrl.ignore(" -up")

    def update(self, time: float, dt: float) -> None:
        """Advance kinetic-navigation state by one tick.

        Computes the desired velocity vector and forwards it to the physics
        controller. Updates the controller's animation state based on whether
        the entity is moving.

        Args:
            time: Current simulation time (seconds, unused here).
            dt: Elapsed time since the previous tick (seconds).
        """
        is_moving = False
        speed = LVector3d(0, 0, 0)
        y = self.key_map['up'] - self.key_map['down']
        if y:
            speed.set_y(y * self.speed * self.speed_factor)
            is_moving = True

        if self.key_map['left']:
            self.turn(self.rot_step_per_sec * dt)

        if self.key_map['right']:
            self.turn(-self.rot_step_per_sec * dt)

        self.set_speed_relative(speed)

        if is_moving:
            self.controller.set_state('moving')
        else:
            self.controller.set_state('idle')

    def set_speed_relative(self, speed: LVector3d) -> None:
        """Forward a velocity vector to the physics controller.

        Args:
            speed: Desired velocity in the controller's local frame
                (LVector3d).
        """
        self.controller.set_speed_relative(speed)

    def turn(self, angle: float) -> None:
        """Rotate the controlled entity by *angle* radians around its up axis.

        Args:
            angle: Rotation amount in radians (positive = left).
        """
        self.controller.turn_relative(angle)
