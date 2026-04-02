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
from typing import TYPE_CHECKING, Dict, Optional

from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import LPoint3d, LQuaterniond, LVector3d

from .. import settings
from .base import NavigationController

if TYPE_CHECKING:
    from direct.showbase import DirectObject

    from ..objects.stellarobject import StellarObject

logger = logging.getLogger("nav")


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
