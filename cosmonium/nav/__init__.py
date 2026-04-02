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

"""Navigation controller package.

The nav package provides the hierarchy of navigation controllers used to
translate user input into camera and scene-body movement:

* :class:`~cosmonium.nav.base.NavigationController` — abstract base class.
* :class:`~cosmonium.nav.interactive.InteractiveNavigationController` — shared
  keyboard/mouse input machinery.
* :class:`~cosmonium.nav.free.FreeNav` — 6-DOF free-flight controller.
* :class:`~cosmonium.nav.walk.WalkNav` — surface-walk controller.
* :class:`~cosmonium.nav.control.ControlNav` — direct body-control controller.
* :class:`~cosmonium.nav.kinetic.KineticNav` — physics-driven controller.
"""

from .base import NavigationController
from .control import ControlNav
from .free import FreeNav
from .interactive import InteractiveNavigationController
from .kinetic import KineticNav
from .walk import WalkNav

__all__ = [
    'NavigationController',
    'InteractiveNavigationController',
    'FreeNav',
    'WalkNav',
    'ControlNav',
    'KineticNav',
]
