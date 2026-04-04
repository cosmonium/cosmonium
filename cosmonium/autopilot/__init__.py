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

"""Autopilot package for smooth camera navigation in Cosmonium.

Architecture
------------
:class:`AutoPilotBase` (in ``base.py``) is the concrete base class that owns
the animation infrastructure (intervals, easing, coordinate helpers).

Autopilot *modes* are separate classes that hold a reference to the base and
call its primitives:

* :class:`NavigationAutoPilot` (``navigation.py``) – destination commands
* :class:`AlignmentAutoPilot` (``alignment.py``) – roll alignment
* :class:`ContinuousAutoPilot` (``continuous.py``) – orbit / rotate / zoom

:class:`AutoPilot` (``autopilot.py``) extends ``AutoPilotBase`` and creates
the standard mode objects as attributes (``navigation``, ``alignment``,
``continuous``).  New modes can be attached without modifying ``AutoPilot``.

The :class:`AutoPilot` name is re-exported here so that existing imports of
the form ``from cosmonium.autopilot import AutoPilot`` continue to work
without any changes.
"""

from .autopilot import AutoPilot

__all__ = ['AutoPilot']
