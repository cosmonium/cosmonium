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


try:
    from cosmonium_engine import TessellationInfo as CTessellationInfo
    from cosmonium_engine import UVPatchGenerator, QCSPatchGenerator, ImprovedQCSPatchGenerator, TilePatchGenerator

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
    print("WARNING: Could not load geometry C implementation, fallback on python implementation")
    print("\t", e)
    from .pygeometry.geometry import UVPatch  # noqa: F401
    from .pygeometry.geometry import SquaredDistanceSquarePatch  # noqa: F401
    from .pygeometry.geometry import NormalizedSquarePatch  # noqa: F401
    from .pygeometry.geometry import Tile  # noqa: F401
    from .pygeometry.geometry import TessellationInfo  # noqa: F401

from .pygeometry.geometry import BoundingBoxGeom  # noqa: F401
from .pygeometry.geometry import UVSphere, IcoSphere  # noqa: F401
from .pygeometry.geometry import RingFaceGeometry  # noqa: F401
from .pygeometry.geometry import UVPatchOffsetVector, UVPatchPoint, UVPatchAABB, halfSphereAABB  # noqa: F401
from .pygeometry.geometry import NormalizedSquarePatchOffsetVector, NormalizedSquarePatchPoint  # noqa: F401
from .pygeometry.geometry import NormalizedSquarePatchAABB  # noqa: F401
from .pygeometry.geometry import SquaredDistanceSquarePatchOffsetVector, SquaredDistanceSquarePatchPoint  # noqa: F401
from .pygeometry.geometry import SquaredDistanceSquarePatchAABB  # noqa: F401
from .pygeometry.geometry import Patch, PatchAABB  # noqa: F401
from .pygeometry.ui import FrameGeom  # noqa: F401
