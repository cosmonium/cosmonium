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

"""AutoPilot class – composes autopilot modes on top of the base.

:class:`AutoPilot` extends :class:`AutoPilotBase` and creates the standard
autopilot mode objects (:attr:`navigation`, :attr:`alignment`,
:attr:`continuous`).  New modes can be added by attaching additional mode
objects without modifying this class.
"""

from __future__ import annotations

from .alignment import AlignmentAutoPilot
from .base import AutoPilotBase
from .continuous import ContinuousAutoPilot
from .navigation import NavigationAutoPilot


class AutoPilot(AutoPilotBase):
    """Autopilot for smooth camera navigation in the simulation.

    Extends :class:`AutoPilotBase` with the standard autopilot mode objects:

    * :attr:`navigation` – destination commands (go_to_front, go_to_object, …)
    * :attr:`alignment`  – reference-frame roll alignment (ecliptic, equatorial)
    * :attr:`continuous`  – time-limited orbit, rotate and zoom operations

    Each mode object holds a back-reference to this autopilot and calls the
    base animation primitives (:meth:`move_and_rotate_to`, :meth:`update_func`,
    etc.) to drive its operations.

    New autopilot modes can be added by creating a mode class and attaching an
    instance — no changes to ``AutoPilot`` are needed.
    """

    def __init__(self, ui) -> None:
        super().__init__(ui)
        self.navigation = NavigationAutoPilot(self)
        self.alignment = AlignmentAutoPilot(self)
        self.continuous = ContinuousAutoPilot(self)
