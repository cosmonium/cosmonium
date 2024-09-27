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


# Coordinate System
# Panda3D Coordinate system : Z-Up Right-handed
#    x : right
#    y : forward (into screen)
#    z : up
# Mapped onto J2000.0 Ecliptic frame
#    x : vernal equinox
#    y :
#    z : North Pole
#
# Celestia and SpaceEngine are Y-Up Right-handed
#    Panda3d = Cel/SE
#      x    =    x
#      y    =    z
#      z    =   -y

try:
    from cosmonium_engine import AnchorReferenceFrame
    from cosmonium_engine import J2000EclipticReferenceFrame, J2000EquatorialReferenceFrame
    from cosmonium_engine import CelestialReferenceFrame, RelativeReferenceFrame
    from cosmonium_engine import StellarAnchorReferenceFrame, OrbitReferenceFrame
    from cosmonium_engine import EquatorialReferenceFrame, SynchroneReferenceFrame
    from cosmonium_engine import J2000BarycentricEclipticReferenceFrame
    from cosmonium_engine import J2000BarycentricEquatorialReferenceFrame
except ImportError as e:
    print("WARNING: Could not load frames C implementation, fallback on python implementation")
    print("\t", e)
    from .pyastro.frame import AnchorReferenceFrame  # noqa: F401
    from .pyastro.frame import J2000EclipticReferenceFrame, J2000EquatorialReferenceFrame  # noqa: F401
    from .pyastro.frame import CelestialReferenceFrame, RelativeReferenceFrame  # noqa: F401
    from .pyastro.frame import OrbitReferenceFrame  # noqa: F401
    from .pyastro.frame import EquatorialReferenceFrame, SynchroneReferenceFrame  # noqa: F401
    from .pyastro.frame import J2000BarycentricEclipticReferenceFrame  # noqa: F401
    from .pyastro.frame import J2000BarycentricEquatorialReferenceFrame  # noqa: F401

    StellarAnchorReferenceFrame = AnchorReferenceFrame

BodyReferenceFrames = (AnchorReferenceFrame, StellarAnchorReferenceFrame)

AbsoluteReferenceFrame = J2000BarycentricEclipticReferenceFrame
