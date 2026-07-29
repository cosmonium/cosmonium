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


try:
    from cosmonium_engine import ImprovedQCSPatchGenerator, QCSPatchGenerator
    from cosmonium_engine import TessellationInfo as CTessellationInfo
    from cosmonium_engine import TilePatchGenerator, UVPatchGenerator

    TessellationInfo = CTessellationInfo
    uv_patch_generator = UVPatchGenerator()
    UVPatch = uv_patch_generator.make
    qcs_patch_generator = QCSPatchGenerator()
    NormalizedSquarePatch = qcs_patch_generator.make
    improved_qcs_patch_generator = ImprovedQCSPatchGenerator()
    SquaredDistanceSquarePatch = improved_qcs_patch_generator.make
    tile_patch_generator = TilePatchGenerator()
    Tile = tile_patch_generator.make
except ImportError as e:
    import logging

    logging.warning("Could not load geometry C++ implementation, fallback on Python implementation")
    logging.warning(e)
    from .pygeometry.cube_patches import SquaredDistanceSquarePatch
    from .pygeometry.cube_patches import NormalizedSquarePatch
    from .pygeometry.tessellation import TessellationInfo
    from .pygeometry.tiles import Tile
    from .pygeometry.uv_patches import UVPatch

from .pygeometry.cube_patches import (
    NormalizedSquarePatchBoundingPoints,
    NormalizedSquarePatchNormal,
    NormalizedSquarePatchOffsetVector,
    NormalizedSquarePatchPoint,
    SquaredDistanceSquarePatchBoundingPoints,
    SquaredDistanceSquarePatchNormal,
    SquaredDistanceSquarePatchOffsetVector,
    SquaredDistanceSquarePatchPoint,
    SquarePatch,
)
from .pygeometry.primitives import BoundingBoxGeom, BoundingBoxGeomUpdate, CubeGeom
from .pygeometry.rings import RingFaceGeometry
from .pygeometry.spheres import DisplacementUVSphere, IcoSphere, UVPatchedSphere, UVSphere
from .pygeometry.tiles import Patch, PatchBoundingPoints, QuadPatch, TileBoundingPoints
from .pygeometry.ui import FrameGeom
from .pygeometry.uv_patches import (
    UVPatchBoundingPoints,
    UVPatchNormal,
    UVPatchOffsetVector,
    UVPatchPoint,
)

__all__ = [
    # Primitives
    "BoundingBoxGeom",
    "BoundingBoxGeomUpdate",
    "CubeGeom",
    # Spheres
    "UVSphere",
    "DisplacementUVSphere",
    "UVPatchedSphere",
    "IcoSphere",
    # UV Patches
    "UVPatch",
    "UVPatchPoint",
    "UVPatchNormal",
    "UVPatchOffsetVector",
    "UVPatchBoundingPoints",
    # Cube patches
    "SquarePatch",
    "SquaredDistanceSquarePatch",
    "SquaredDistanceSquarePatchPoint",
    "SquaredDistanceSquarePatchNormal",
    "SquaredDistanceSquarePatchOffsetVector",
    "SquaredDistanceSquarePatchBoundingPoints",
    "NormalizedSquarePatch",
    "NormalizedSquarePatchPoint",
    "NormalizedSquarePatchNormal",
    "NormalizedSquarePatchOffsetVector",
    "NormalizedSquarePatchBoundingPoints",
    # Tiles
    "Tile",
    "TileBoundingPoints",
    "Patch",
    "PatchBoundingPoints",
    "QuadPatch",
    # Tessellation
    "TessellationInfo",
    # Rings
    "RingFaceGeometry",
    # UI
    "FrameGeom",
]
