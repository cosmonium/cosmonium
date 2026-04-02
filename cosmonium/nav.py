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

import logging
import sys
from abc import ABC, abstractmethod
from math import exp, pi
from typing import TYPE_CHECKING, Dict, Optional

from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import LPoint3d, LQuaterniond, LVector3d

from . import settings
from .astro import units

if TYPE_CHECKING:
    from direct.showbase import DirectObject
    from direct.showbase.ShowBase import ShowBase

    from .camera.base import CameraController, CameraHolder
    from .controllers.base import MovementController
    from .objects.stellarobject import StellarObject

logger = logging.getLogger("nav")


class NavigationController(ABC):
    """Abstract base class for all navigation controllers.

    A navigation controller translates user input (keyboard, mouse, etc.) into
    camera and scene-body movement.  Subclasses override :meth:`register_events`,
    :meth:`remove_events`, and :meth:`update` to provide concrete behaviour.
    """

    def __init__(self) -> None:
        self.base: Optional[ShowBase] = None
        self.camera: Optional[CameraHolder] = None
        self.camera_controller: Optional[CameraController] = None
        self.controller: Optional[MovementController] = None

    def init(
        self, base: ShowBase, camera: CameraHolder, camera_controller: CameraController, controller: MovementController
    ) -> None:
        self.base = base
        self.camera = camera
        self.camera_controller = camera_controller
        self.controller = controller

    def set_target(self, target: StellarObject) -> None:
        """Set the navigation target (e.g. a celestial body for surface walk).

        The base implementation is a no-op. Subclasses that require a target
        (i.e. require_target returns True) must override this method.

        Args:
            target: The target scene object.
        """

    @abstractmethod
    def get_name(self) -> str:
        """Return a human-readable name for this navigation mode.

        Returns:
            Display name string.
        """

    @abstractmethod
    def get_id(self) -> str:
        """Return the identifier for this navigation mode.

        Returns:
            Identifier string.
        """

    def require_target(self) -> bool:
        """Whether this controller requires a target body to be active.

        Returns:
            True if a target must be provided before activation.
        """
        return False

    def require_controller(self) -> bool:
        """Whether this controller requires a movement controller to be active.

        Returns:
            True if a movement controller must be provided.
        """
        return False

    @abstractmethod
    def register_events(self, event_ctrl: DirectObject) -> None:
        """Attach input event handlers.

        Args:
            event_ctrl: An object that exposes accept(event, callback, args)
                (typically the Panda3D ShowBase instance).

        Note:
            Each call to register_events **must** be paired with a
            corresponding call to remove_events when this controller is
            deactivated to avoid stale event handlers.
            Instead of relying on the event_ctrl, this class should inherit
            from DirectObject and use its own event handler.
        """

    @abstractmethod
    def remove_events(self, event_ctrl: DirectObject) -> None:
        """Detach previously registered input event handlers.

        Args:
            event_ctrl: The same object passed to register_events.
        """

    def set_controller(self, controller: MovementController) -> None:
        """Replace the movement controller.

        Args:
            controller: New movement controller.
        """
        self.controller = controller

    def set_camera_controller(self, camera_controller: CameraController) -> None:
        """Replace the camera orientation controller.

        Args:
            camera_controller: New camera controller.
        """
        self.camera_controller = camera_controller

    def stash_position(self) -> None:
        """Convert internally tracked positions to absolute frame before a
        reference point change (called by the engine on anchor switches).

        The base implementation is a no-op. Subclasses that track positions
        (e.g. InteractiveNavigationController) override this method.
        """

    def pop_position(self) -> None:
        """Convert internally tracked positions back to the local frame after a
        reference-frame change.

        The base implementation is a no-op. Subclasses that track positions
        (e.g. InteractiveNavigationController) override this method.
        """

    def update(self, time: float, dt: float) -> None:
        """Advance the navigation state for one simulation tick.

        The base implementation is a no-op. Concrete navigation controllers
        must override this method to process input and move the observer.

        Args:
            time: Current simulation time (seconds).
            dt: Elapsed time since the previous tick (seconds).
        """


class InteractiveNavigationController(NavigationController):
    """Base class for navigation controllers that respond to keyboard and mouse.

    Provides shared machinery for:

    * A key-state map (``key_map``) updated via :meth:`set_key`.
    * Mouse-wheel debouncing (``wheel_event_time`` / ``wheel_event_duration``).
    * Orbit computations used by :meth:`create_orbit_params` / :meth:`do_orbit`.
    * Reference-frame stash/pop helpers for anchor switches.
    """

    #: How long (in seconds) a single wheel tick is considered "active".
    wheel_event_duration = 0.1

    def __init__(self) -> None:
        NavigationController.__init__(self)
        self.key_map: Dict[str, int] = {}
        self.orbit_center = LPoint3d()
        self.orbit_start: Optional[LVector3d] = None
        self.orbit_orientation: Optional[LQuaterniond] = None
        self.wheel_event_time = 0.0
        self.wheel_direction = 0.0

    def set_key(self, key: str, state: int, *extra_keys: str) -> None:
        """Update one or more entries in the key-state map.

        This method is used as a key event callback. The *primary* key is
        always set to *state*, and any additional *extra_keys* are also set to
        *state* (useful for clearing composite modifiers on key-up events).

        Args:
            key: Primary key name (must exist in key_map).
            state: Integer state value — 1 for pressed, 0 for released.
            *extra_keys: Optional additional key names to set to *state*.
        """
        self.key_map[key] = state
        for extra in extra_keys:
            self.key_map[extra] = state

    def register_wheel_events(self, event_ctrl: DirectObject) -> None:
        """Register mouse-wheel up/down events.

        Args:
            event_ctrl: Event controller (ShowBase instance).
        """
        event_ctrl.accept("wheel_up", self.wheel_event, [1])
        event_ctrl.accept("wheel_down", self.wheel_event, [-1])

    def remove_wheel_events(self, event_ctrl: DirectObject) -> None:
        """Unregister mouse-wheel events previously registered by
        register_wheel_events.

        Args:
            event_ctrl: Event controller (ShowBase instance).
        """
        event_ctrl.ignore("wheel_up")
        event_ctrl.ignore("wheel_down")

    def wheel_event(self, direction: float) -> None:
        """Handle a mouse-wheel tick.

        Records the direction and timestamp so that update can apply
        the scroll for one wheel_event_duration window.

        Args:
            direction: +1 for scroll-up (zoom in), -1 for scroll-down.
        """
        if settings.invert_wheel:
            direction = -direction
        self.wheel_event_time = globalClock.get_real_time()
        self.wheel_direction = direction

    def stash_position(self) -> None:
        """Convert orbit_center to absolute coordinates before an anchor switch."""
        self.orbit_center = self.controller.anchor.calc_absolute_position_of(self.orbit_center)

    def pop_position(self) -> None:
        """Convert orbit_center back to frame-local coordinates after an anchor switch."""
        self.orbit_center = self.controller.anchor.calc_frame_position_of_absolute(self.orbit_center)

    def create_orbit_params(self, target: StellarObject, surface: bool = False) -> None:
        """Initialise orbit state around *target* for a subsequent do_orbit call.

        Orbiting a body involves both the scene object and the camera controller:
        the orbit pivot is stored in the object's local frame to prevent drift as
        the reference frame moves.

        Args:
            target: The celestial body (or other anchor-bearing object) to orbit.
            surface: When True the pivot is placed on the body's surface
                directly below the observer rather than at the body centre.
        """
        center = target.anchor.calc_absolute_relative_position_to(self.controller.get_absolute_reference_point())
        if surface:
            # Place the orbit pivot at the surface of the body beneath the observer.
            center += target.anchor.vector_to_obs * target.anchor._height_under
        self.orbit_center = self.controller.anchor.calc_frame_position_of_local(center)
        self.orbit_start = self.controller.get_frame_position() - self.orbit_center
        if self.controller.orbit_rot_camera:
            self.orbit_orientation = self.camera_controller.get_local_orientation()
        else:
            self.orbit_orientation = self.controller.get_frame_orientation()

    def do_orbit(self, z_angle: float, x_angle: float) -> None:
        """Apply an incremental orbit rotation around the current pivot.

        Two rotations are computed independently:

        1. **Orientation**: rotates the camera (or body) around the pivot using
           self.orbit_orientation as the reference frame.
        2. **Position**: moves the observer along the orbit arc using either the
           object-frame orientation (non-camera orbit) or the frame-converted
           orientation (camera orbit).

        Args:
            z_angle: Rotation angle (radians) around the local *up* axis.
            x_angle: Rotation angle (radians) around the local *right* axis.
        """
        # --- Orientation update ---
        orient_z_rot = LQuaterniond()
        orient_x_rot = LQuaterniond()
        try:
            orbit_z_axis = self.orbit_orientation.xform(LVector3d.up())
            orbit_x_axis = self.orbit_orientation.xform(LVector3d.right())
            orient_z_rot.set_from_axis_angle_rad(z_angle, orbit_z_axis)
            orient_x_rot.set_from_axis_angle_rad(x_angle, orbit_x_axis)
        except AssertionError as e:
            logger.warning("do_orbit: invalid orientation axis: %s", e)
        combined_orient = orient_x_rot * orient_z_rot
        new_rot = self.orbit_orientation * combined_orient
        if self.controller.orbit_rot_camera:
            self.camera_controller.set_local_orientation(new_rot)
        else:
            self.controller.set_frame_orientation(new_rot)

        # --- Position update (independent rotation computation) ---
        pos_z_rot = LQuaterniond()
        pos_x_rot = LQuaterniond()
        try:
            if self.controller.orbit_rot_camera:
                orbit_orientation = self.controller.anchor.calc_frame_orientation_of(self.orbit_orientation)
            else:
                orbit_orientation = self.orbit_orientation
            orbit_z_axis = orbit_orientation.xform(LVector3d.up())
            orbit_x_axis = orbit_orientation.xform(LVector3d.right())
            pos_z_rot.set_from_axis_angle_rad(z_angle, orbit_z_axis)
            pos_x_rot.set_from_axis_angle_rad(x_angle, orbit_x_axis)
        except AssertionError as e:
            logger.warning("do_orbit: invalid position axis: %s", e)
        combined_pos = pos_x_rot * pos_z_rot
        delta = combined_pos.xform(self.orbit_start)
        self.controller.set_frame_position(delta + self.orbit_center)


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
    * **a** (hold) — activate fast movement (10× speed).

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
        """Engage fast movement (10× base speed)."""
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
        (_lon, _lat, normal) = self.body.get_tangent_plane_under(object_position)
        surface_point = self.body.get_point_under(self.controller.get_local_position())
        direction = self.controller.get_local_position() - surface_point
        altitude = direction.dot(normal)
        direction = self.controller.get_absolute_orientation().xform(LVector3d.forward())
        projected = direction - normal * direction.dot(normal)
        projected.normalize()
        new_position = self.body.get_point_under(object_position + projected * distance)
        (_lon, _lat, normal) = self.body.get_tangent_plane_under(new_position)
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
        (tangent, binormal, normal) = self.body.get_tangent_plane_under(self.controller.get_local_position())
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
