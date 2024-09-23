#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
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

from .editors import ObjectEditors

from .objecteditor import StellarObjectEditor
from .orbiteditor import EllipticalOrbitEditor
from .rotationeditor import UniformRotationEditor

from ...objects.stellarobject import StellarObject
from ...astro.orbits import EllipticalOrbit
from ...astro.rotations import UniformRotation

ObjectEditors.register(StellarObject, StellarObjectEditor)
ObjectEditors.register(EllipticalOrbit, EllipticalOrbitEditor)
ObjectEditors.register(UniformRotation, UniformRotationEditor)
