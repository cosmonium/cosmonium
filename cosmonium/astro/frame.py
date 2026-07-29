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
    from cosmonium_engine import (
        AnchorReferenceFrame,
        CelestialReferenceFrame,
        EquatorialReferenceFrame,
        J2000BarycentricEclipticReferenceFrame,
        J2000BarycentricEquatorialReferenceFrame,
        J2000EclipticReferenceFrame,
        J2000EquatorialReferenceFrame,
        OrbitReferenceFrame,
        RelativeReferenceFrame,
        StellarAnchorReferenceFrame,
        SynchroneReferenceFrame,
    )
except ImportError as e:
    import logging

    logging.warning("Could not load frames C++ implementation, fallback on Python implementation")
    logging.warning(e)
    from .pyastro.frames.anchors import (
        AnchorReferenceFrame,
        CelestialReferenceFrame,
        J2000EclipticReferenceFrame,
        J2000EquatorialReferenceFrame,
    )
    from .pyastro.frames.base import (
        J2000BarycentricEclipticReferenceFrame,
        J2000BarycentricEquatorialReferenceFrame,
        ReferenceFrame,
    )
    from .pyastro.frames.relative import RelativeReferenceFrame
    from .pyastro.frames.stellars import (
        EquatorialReferenceFrame,
        OrbitReferenceFrame,
        StellarAnchorReferenceFrame,
        SynchroneReferenceFrame,
    )
BodyReferenceFrames = (AnchorReferenceFrame, StellarAnchorReferenceFrame)

AbsoluteReferenceFrame = J2000BarycentricEclipticReferenceFrame


__all__ = [
    'AbsoluteReferenceFrame',
    'BodyReferenceFrames',
    'AnchorReferenceFrame',
    'CelestialReferenceFrame',
    'EquatorialReferenceFrame',
    'ReferenceFrame',
    'J2000BarycentricEclipticReferenceFrame',
    'J2000BarycentricEquatorialReferenceFrame',
    'J2000EclipticReferenceFrame',
    'J2000EquatorialReferenceFrame',
    'OrbitReferenceFrame',
    'RelativeReferenceFrame',
    'StellarAnchorReferenceFrame',
    'SynchroneReferenceFrame',
]
