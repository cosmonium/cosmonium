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

"""Time-limited continuous camera movements for the autopilot.

Provides :class:`ContinuousAutoPilot`, which drives per-frame callbacks for
orbiting around an object, rotating in place, and changing the viewing
distance.  All operations are executed via
:meth:`AutoPilotBase.update_func`.
"""

from __future__ import annotations

from math import exp, log
from typing import TYPE_CHECKING, Optional

from panda3d.core import LQuaterniond, LVector3d

from .. import settings

if TYPE_CHECKING:
    from .base import AutoPilotBase


class ContinuousAutoPilot:
    """Autopilot mode for time-limited continuous movements.

    Holds a reference to an :class:`~cosmonium.autopilot.base.AutoPilotBase`
    instance whose :meth:`~AutoPilotBase.update_func` is used to run the
    per-frame callbacks.

    Args:
        autopilot: The base autopilot that provides animation infrastructure.
    """

    def __init__(self, autopilot: AutoPilotBase) -> None:
        self.autopilot = autopilot

    # ------------------------------------------------------------------
    # Distance change (exponential zoom)
    # ------------------------------------------------------------------

    def do_change_distance(self, delta: float, rate: float) -> None:
        """Per-frame callback for exponential distance change toward the selected object.

        Applies an exponential zoom so that the *rate* of change feels
        uniform in log-space (similar to a dolly move on a logarithmic
        scale).  Movement is clamped so the camera cannot pass through the
        object.

        The "natural distance" used as a reference for the log-space
        computation is ``settings.goto_natural_distance_multiplier`` times
        the object's minimum approach distance.

        Args:
            delta: Elapsed time in seconds since the last call.
            rate: Zoom rate (positive = move away, negative = move closer).
        """
        target = self.autopilot.ui.selected
        center = target.anchor.calc_absolute_relative_position_to(
            self.autopilot.controller.get_absolute_reference_point()
        )
        min_distance = target.get_apparent_radius()
        natural_distance = settings.goto_natural_distance_multiplier * min_distance
        relative_pos = self.autopilot.controller.get_local_position() - center

        # If already inside the minimum distance, halve it to avoid
        # locking the camera in place.
        if target.anchor.distance_to_obs < min_distance:
            min_distance = target.anchor.distance_to_obs * 0.5

        if target.anchor.distance_to_obs >= min_distance and natural_distance != 0:
            r = (target.anchor.distance_to_obs - min_distance) / natural_distance
            new_distance = min_distance + natural_distance * exp(log(r) + rate * delta)
            new_pos = relative_pos * (new_distance / target.anchor.distance_to_obs)
            self.autopilot.controller.set_local_position(center + new_pos)

    def change_distance(self, rate: float, duration: Optional[float] = None) -> None:
        """Zoom in or out relative to the selected object over *duration* seconds.

        Args:
            rate: Zoom rate (positive = move away, negative = move closer).
            duration: Duration of the zoom operation.  Defaults to ``settings.fast_move``.
        """
        if duration is None:
            duration = settings.fast_move
        self.autopilot.update_func(self.do_change_distance, duration, (rate,))

    # ------------------------------------------------------------------
    # Orbit around selected object
    # ------------------------------------------------------------------

    def do_orbit(self, delta: float, axis: LVector3d, rate: float) -> None:
        """Per-frame callback that rotates the camera around the selected object.

        The camera is orbited about the object's centre in frame space.
        The orbit rotation is applied both to the camera position (to move
        it around the object) and to the camera orientation (to keep the
        object centred in the view).

        Args:
            delta: Elapsed time in seconds since the last call.
            axis: World-space rotation axis.
            rate: Angular velocity in radians per second.
        """
        target = self.autopilot.ui.selected
        center = target.anchor.calc_absolute_relative_position_to(
            self.autopilot.controller.get_absolute_reference_point()
        )
        center = self.autopilot.controller.anchor.calc_frame_position_of_local(center)
        relative_pos = self.autopilot.controller.get_frame_position() - center
        rot = LQuaterniond()
        rot.setFromAxisAngleRad(rate * delta, axis)
        # Transform the world-space rotation into the camera's local frame.
        frame_orient = self.autopilot.controller.get_frame_orientation()
        rot_local = frame_orient.conjugate() * rot * frame_orient
        rot_local.normalize()
        # Rotate the relative position and update camera position.
        distance = relative_pos.length()
        relative_pos.normalize()
        new_pos = rot_local.xform(relative_pos) * distance
        self.autopilot.controller.set_frame_position(new_pos + center)
        # Apply the same rotation to the camera orientation so it keeps the object in the centre of the view.
        self.autopilot.controller.turn_local(frame_orient * rot_local)

    def orbit(self, axis: LVector3d, rate: float, duration: Optional[float] = None) -> None:
        """Orbit the camera around the selected object for *duration* seconds.

        Args:
            axis: World-space rotation axis.
            rate: Angular velocity in radians per second.
            duration: Duration of the orbit.  Defaults to ``settings.slow_move``.
        """
        if duration is None:
            duration = settings.slow_move
        self.autopilot.update_func(self.do_orbit, duration, [axis, rate])

    # ------------------------------------------------------------------
    # In-place rotation
    # ------------------------------------------------------------------

    def do_rotate(self, delta: float, axis: LVector3d, rate: float) -> None:
        """Per-frame callback that rotates the camera in place.

        Args:
            delta: Elapsed time in seconds since the last call.
            axis: Local-space rotation axis.
            rate: Angular velocity in radians per second.
        """
        rot = LQuaterniond()
        rot.setFromAxisAngleRad(rate * delta, axis)
        self.autopilot.controller.step_turn_local(rot)

    def rotate(self, axis: LVector3d, rate: float, duration: Optional[float] = None) -> None:
        """Rotate the camera in place for *duration* seconds.

        Args:
            axis: Local-space rotation axis.
            rate: Angular velocity in radians per second.
            duration: Duration of the rotation.  Defaults to ``settings.slow_move``.
        """
        if duration is None:
            duration = settings.slow_move
        self.autopilot.update_func(self.do_rotate, duration, [axis, rate])
