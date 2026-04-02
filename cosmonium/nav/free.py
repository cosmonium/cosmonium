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
from math import exp, pi
from typing import TYPE_CHECKING

from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import LQuaterniond, LVector3d

from .. import settings
from .interactive import InteractiveNavigationController

if TYPE_CHECKING:
    from direct.showbase import DirectObject

    from ..objects.stellarobject import StellarObject


class FreeNav(InteractiveNavigationController):
    """Free-flight navigation controller.

    Provides 6-DOF movement through space:

    * **Arrow keys** — pitch and yaw (direction follows the ``celestia_nav``
      setting for compatibility with Celestia-style controls).
    * **Ctrl + left/right** (or **Alt** on macOS) — roll.
    * **Home / End** (or mouse-wheel) — move forward/backward along the
      current heading.
    * **a / z** — exponentially accelerate or decelerate forward motion.
    * **q** — reverse the current travel direction.
    * **s** — stop forward motion.
    * **x** — align the camera to the natural body-up axis.
    * **Shift + arrow keys** — keyboard-driven orbit around the selected body.
    * **Right mouse button** (hold + drag) — mouse orbit around the selected body.
    * **Shift + right mouse button** — mouse orbit anchored to the surface point
      directly below the observer.
    """

    #: Rate of altitude change per unit time when Home/End/wheel is pressed.
    distance_speed = 2.0
    #: Maximum angular speed (rad/s) for keyboard pitch/yaw/roll.
    rotation_speed = 2 * pi / 3
    #: Exponential damping coefficient applied to rotational velocity each tick.
    rotation_damping = 2.0

    def __init__(self) -> None:
        InteractiveNavigationController.__init__(self)
        self.speed: float = 0.0
        self.rot_speed = LVector3d()
        self.mouse_orbit = False
        self.keyboard_track = False
        self.start_x = 0.0
        self.start_y = 0.0
        self.orbit_coef = 0.0
        self.orbit_x = 0.0
        self.orbit_z = 0.0

    def get_name(self) -> str:
        """Return the human-readable name for this navigation mode.

        Returns:
            Display name string.
        """
        return 'Free navigation'

    def get_id(self) -> str:
        """Return the stable identifier for this navigation mode.

        Returns:
            Short ASCII identifier string.
        """
        return 'free'

    def register_events(self, event_ctrl: DirectObject) -> None:
        """Register all keyboard and mouse events for free-flight navigation."""
        self.key_map = {
            "left": 0,
            "right": 0,
            "up": 0,
            "down": 0,
            "home": 0,
            "end": 0,
            "control-left": 0,
            "control-right": 0,
            "shift-left": 0,
            "shift-right": 0,
            "shift-up": 0,
            "shift-down": 0,
            "a": 0,
            "z": 0,
        }
        event_ctrl.accept("arrow_up", self.set_key, ['up', 1])
        event_ctrl.accept("arrow_up-up", self.set_key, ['up', 0, 'shift-up'])
        event_ctrl.accept("arrow_down", self.set_key, ['down', 1])
        event_ctrl.accept("arrow_down-up", self.set_key, ['down', 0, 'shift-down'])
        event_ctrl.accept("shift-arrow_up", self.set_key, ['shift-up', 1])
        event_ctrl.accept("shift-arrow_down", self.set_key, ['shift-down', 1])
        event_ctrl.accept("arrow_left", self.set_key, ['left', 1])
        event_ctrl.accept("arrow_left-up", self.set_key, ['left', 0, 'shift-left', 'control-left'])
        event_ctrl.accept("arrow_right", self.set_key, ['right', 1])
        event_ctrl.accept("arrow_right-up", self.set_key, ['right', 0, 'shift-right', 'control-right'])
        event_ctrl.accept("shift-arrow_left", self.set_key, ['shift-left', 1])
        event_ctrl.accept("shift-arrow_right", self.set_key, ['shift-right', 1])
        if sys.platform != "darwin":
            event_ctrl.accept("control-arrow_left", self.set_key, ['control-left', 1])
            event_ctrl.accept("control-arrow_right", self.set_key, ['control-right', 1])
        else:
            # macOS: Ctrl+arrow is intercepted by the OS; use Alt instead.
            event_ctrl.accept("alt-arrow_left", self.set_key, ['control-left', 1])
            event_ctrl.accept("alt-arrow_right", self.set_key, ['control-right', 1])
        event_ctrl.accept("home", self.set_key, ['home', 1])
        event_ctrl.accept("home-up", self.set_key, ['home', 0])
        event_ctrl.accept("end", self.set_key, ['end', 1])
        event_ctrl.accept("end-up", self.set_key, ['end', 0])
        event_ctrl.accept("a", self.set_key, ['a', 1])
        event_ctrl.accept("a-up", self.set_key, ['a', 0])
        event_ctrl.accept("z", self.set_key, ['z', 1])
        event_ctrl.accept("z-up", self.set_key, ['z', 0])
        event_ctrl.accept("q", self.switch_direction)
        event_ctrl.accept("s", self.stop)
        event_ctrl.accept("x", self.align_camera)

        event_ctrl.accept("mouse3", self.on_orbit_click, [False])
        event_ctrl.accept("shift-mouse3", self.on_orbit_click, [True])
        event_ctrl.accept("mouse3-up", self.on_orbit_release)

        self.register_wheel_events(event_ctrl)

    def remove_events(self, event_ctrl):
        """Unregister all events registered by register_events."""
        event_ctrl.ignore("arrow_up")
        event_ctrl.ignore("arrow_up-up")
        event_ctrl.ignore("arrow_down")
        event_ctrl.ignore("arrow_down-up")
        event_ctrl.ignore("shift-arrow_up")
        event_ctrl.ignore("shift-arrow_down")
        event_ctrl.ignore("arrow_left")
        event_ctrl.ignore("arrow_left-up")
        event_ctrl.ignore("arrow_right")
        event_ctrl.ignore("arrow_right-up")
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
        event_ctrl.ignore("a")
        event_ctrl.ignore("a-up")
        event_ctrl.ignore("z")
        event_ctrl.ignore("z-up")
        event_ctrl.ignore("q")
        event_ctrl.ignore("s")
        event_ctrl.ignore("x")

        event_ctrl.ignore("mouse3")
        event_ctrl.ignore("shift-mouse3")
        event_ctrl.ignore("mouse3-up")

        self.remove_wheel_events(event_ctrl)

    def select_target(self) -> StellarObject | None:
        """Return the best available navigation target.

        Priority: followed body > synchronised body > selected body > None.

        Returns:
            The current target object, or None if none is available.
        """
        if self.base.follow is not None:
            return self.base.follow
        if self.base.sync is not None:
            return self.base.sync
        if self.base.selected is not None:
            return self.base.selected
        return None

    def switch_direction(self) -> None:
        """Reverse the current forward-travel direction."""
        self.speed = -self.speed

    def stop(self) -> None:
        """Bring forward motion to an immediate halt."""
        self.speed = 0

    def align_camera(self) -> None:
        """Align the camera orientation to the natural up axis of the reference body."""
        self.camera_controller.prepare_movement()

    def on_orbit_click(self, orbit_surface: bool) -> None:
        """Begin a mouse-drag orbit when the right mouse button is pressed.

        If *orbit_surface* is True the pivot is placed on the body surface;
        otherwise it is placed at the body centre with the orbit angular speed
        automatically scaled to the body's apparent size on screen.

        Args:
            orbit_surface: True to orbit around the surface point beneath
                the observer; False to orbit around the body centre.
        """
        if not self.base.mouseWatcherNode.hasMouse():
            return
        mpos = self.base.mouseWatcherNode.getMouse()
        self.start_x = mpos.get_x()
        self.start_y = mpos.get_y()
        target = self.select_target()
        if target is not None:
            self.mouse_orbit = True
            if orbit_surface:
                # Constant angular speed when orbiting a surface point.
                self.orbit_angle_x = pi / 3
                self.orbit_angle_y = pi / 3
            else:
                # Scale angular speed so that orbit remains manageable at any
                # distance from the body.
                arc_length = pi * target.get_apparent_radius()
                apparent_size = arc_length / (
                    (target.anchor.distance_to_obs - target.anchor._height_under) * self.camera.pixel_size
                )
                if apparent_size != 0.0:
                    self.orbit_angle_x = min(pi, pi / 2 / apparent_size * self.camera.height)
                    self.orbit_angle_y = min(pi, pi / 2 / apparent_size * self.camera.width)
                else:
                    # Body has no measurable surface; fall back to constant speed.
                    self.orbit_angle_x = pi
                    self.orbit_angle_y = pi
            self.create_orbit_params(target, orbit_surface)

    def on_orbit_release(self) -> None:
        """End the mouse-drag orbit when the right mouse button is released."""
        self.mouse_orbit = False

    def update(self, time: float, dt: float) -> None:
        """Advance free-navigation state by one tick.

        Processes mouse orbit, keyboard rotation/translation, keyboard orbit,
        forward-speed acceleration, damped rotation, and altitude changes.

        Args:
            time: Current simulation time (seconds, unused here).
            dt: Elapsed time since the previous tick (seconds).
        """
        rot_x = 0.0
        rot_y = 0.0
        rot_z = 0.0
        distance = 0.0
        if self.mouse_orbit and self.base.mouseWatcherNode.hasMouse():
            mpos = self.base.mouseWatcherNode.getMouse()
            delta_x = mpos.get_x() - self.start_x
            delta_y = mpos.get_y() - self.start_y
            z_angle = -delta_x * self.orbit_angle_x
            x_angle = delta_y * self.orbit_angle_y
            self.do_orbit(z_angle, x_angle)

        if settings.celestia_nav:
            if self.key_map['up']:
                rot_x = -1
            if self.key_map['down']:
                rot_x = 1
            if self.key_map['left']:
                rot_y = -1
            if self.key_map['right']:
                rot_y = 1
        else:
            if self.key_map['up']:
                rot_x = 1
            if self.key_map['down']:
                rot_x = -1
            if self.key_map['left']:
                rot_y = 1
            if self.key_map['right']:
                rot_y = -1
        if self.key_map['control-left']:
            rot_z = 1
        if self.key_map['control-right']:
            rot_z = -1

        if self.key_map['home']:
            distance = 1
        if self.key_map['end']:
            distance = -1

        if self.wheel_event_time + self.wheel_event_duration > globalClock.get_real_time():
            distance = self.wheel_direction

        if not self.keyboard_track and (
            self.key_map['shift-left']
            or self.key_map['shift-right']
            or self.key_map['shift-up']
            or self.key_map['shift-down']
        ):
            target = self.select_target()
            if target is not None:
                self.keyboard_track = True
                arc_length = pi * target.get_apparent_radius()
                apparent_size = arc_length / (target.anchor.distance_to_obs - target.anchor._height_under)
                if apparent_size != 0:
                    self.orbit_coef = min(pi, pi / 2 / apparent_size)
                else:
                    self.orbit_coef = pi
                self.orbit_x = 0.0
                self.orbit_z = 0.0
                self.create_orbit_params(target)

        if self.keyboard_track:
            if not (
                self.key_map['shift-left']
                or self.key_map['shift-right']
                or self.key_map['shift-up']
                or self.key_map['shift-down']
            ):
                self.keyboard_track = False

            if self.key_map['shift-left']:
                self.orbit_z += self.orbit_coef * dt
                self.do_orbit(self.orbit_z, self.orbit_x)

            if self.key_map['shift-right']:
                self.orbit_z -= self.orbit_coef * dt
                self.do_orbit(self.orbit_z, self.orbit_x)

            if self.key_map['shift-up']:
                self.orbit_x += self.orbit_coef * dt
                self.do_orbit(self.orbit_z, self.orbit_x)

            if self.key_map['shift-down']:
                self.orbit_x -= self.orbit_coef * dt
                self.do_orbit(self.orbit_z, self.orbit_x)

        if self.key_map['a'] or self.key_map['z'] or rot_x != 0 or rot_y != 0 or rot_z != 0:
            self.camera_controller.prepare_movement()

        if self.key_map['a']:
            if self.speed == 0:
                self.speed = 0.1
            else:
                self.speed *= exp(dt * 3)

        if self.key_map['z']:
            if self.speed < 1e-5:
                self.speed = 0
            else:
                self.speed /= exp(dt * 3)
        y = self.speed * dt
        self.controller.step_relative(y)

        if settings.damped_nav:
            self.rot_speed *= exp(-dt * self.rotation_damping)
            self.rot_speed += LVector3d(rot_x, rot_y, rot_z) * self.rotation_speed * dt
        else:
            self.rot_speed = LVector3d(rot_x, rot_y, rot_z) * self.rotation_speed
        self.turn(LVector3d.right(), self.rot_speed.x * dt)
        self.turn(LVector3d.forward(), self.rot_speed.y * dt)
        self.turn(LVector3d.up(), self.rot_speed.z * dt)
        self.change_altitude(distance * self.distance_speed * dt)

    def turn(self, axis: LVector3d, angle: float) -> None:
        """Apply an incremental rotation around *axis* to the movement controller.

        Args:
            axis: Unit vector (in local frame) to rotate around.
            angle: Rotation amount in radians.
        """
        rot = LQuaterniond()
        rot.setFromAxisAngleRad(angle, axis)
        self.controller.step_turn(rot)

    def change_altitude(self, rate: float) -> None:
        """Move the observer towards or away from the surface of the target body.

        The movement is along the surface normal so that altitude changes cleanly
        on curved surfaces. When the observer would go below the minimum safe
        altitude (settings.min_altitude) it is instead snapped
        to that altitude.

        Args:
            rate: Fractional altitude change per tick; positive moves away
                from the surface, negative moves towards it.
        """
        if rate == 0.0:
            return
        target = self.select_target()
        if target is None:
            return
        local_position = self.controller.anchor.calc_absolute_relative_position_to(
            target.anchor.get_absolute_reference_point()
        )
        (tangent, binormal, normal) = target.get_tangent_plane_under(local_position)
        surface_point = target.get_point_under(local_position)
        direction = local_position - surface_point
        altitude = direction.dot(normal)
        if altitude > 0:
            if rate < 0 or altitude >= settings.min_altitude:
                self.controller.delta_local(-normal * altitude * rate)
        else:
            self.controller.set_local_position(surface_point + settings.min_altitude * normal)
