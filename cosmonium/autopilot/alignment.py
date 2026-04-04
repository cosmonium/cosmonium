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

"""Reference-frame roll alignment for the autopilot.

Provides :class:`AlignmentAutoPilot`, which can roll the camera so that its
up axis aligns with a given reference plane (ecliptic or equatorial).
"""

from __future__ import annotations

from math import acos, pi
from typing import TYPE_CHECKING, Optional

from panda3d.core import LQuaterniond, LVector3d

from ..astro.frame import J2000EclipticReferenceFrame, J2000EquatorialReferenceFrame

if TYPE_CHECKING:
    from .base import AutoPilotBase


class AlignmentAutoPilot:
    """Autopilot mode for reference-frame roll alignment.

    Holds a reference to an :class:`~cosmonium.autopilot.base.AutoPilotBase`
    instance whose controller is used to read the current orientation and
    apply the roll correction.

    Args:
        autopilot: The base autopilot that provides controller access.
    """

    def __init__(self, autopilot: AutoPilotBase) -> None:
        self.autopilot = autopilot

    def _compute_roll_to_align(self, plane_normal: LVector3d) -> LQuaterniond:
        """Compute the roll angle required to align the camera to a reference plane.

        Given the normal of a reference plane (e.g. the ecliptic or
        equatorial plane) expressed in the camera's local frame, returns a
        quaternion representing the roll correction needed to align the
        camera's up axis with that plane.

        Args:
            plane_normal: The plane normal vector, already expressed in the camera's
                local frame (i.e. already transformed by the inverse of the
                frame orientation).

        Returns:
            Roll quaternion around the camera's forward axis.
        """
        angle = acos(plane_normal.dot(LVector3d.right()))
        direction = plane_normal.cross(LVector3d.right()).dot(LVector3d.forward())
        if direction < 0:
            angle = 2 * pi - angle
        rot = LQuaterniond()
        rot.setFromAxisAngleRad(pi / 2 - angle, LVector3d.forward())
        return rot

    def align_on_ecliptic(self, duration: Optional[float] = None) -> None:
        """Roll the camera so its up axis aligns with the J2000 ecliptic plane.

        The alignment is applied instantly regardless of *duration* (animated
        alignment is not yet implemented).

        Args:
            duration: Reserved for future animated alignment support.
        """
        ecliptic_normal = (
            self.autopilot.controller.get_frame_orientation()
            .conjugate()
            .xform(J2000EclipticReferenceFrame().get_orientation().xform(LVector3d.up()))
        )
        rot = self._compute_roll_to_align(ecliptic_normal)
        self.autopilot.controller.step_turn_local(rot)

    def align_on_equatorial(self, duration: Optional[float] = None) -> None:
        """Roll the camera so its up axis aligns with the J2000 equatorial plane.

        The alignment is applied instantly regardless of *duration* (animated
        alignment is not yet implemented).

        Args:
            duration: Reserved for future animated alignment support.
        """
        equatorial_normal = (
            self.autopilot.controller.get_frame_orientation()
            .conjugate()
            .xform(J2000EquatorialReferenceFrame().get_orientation().xform(LVector3d.up()))
        )
        rot = self._compute_roll_to_align(equatorial_normal)
        self.autopilot.controller.step_turn_local(rot)
