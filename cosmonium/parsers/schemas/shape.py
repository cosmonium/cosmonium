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


"""
Shape configuration schemas.

Defines Pydantic models for different shape types including patched shapes,
simple shapes, meshes, billboards, and tiled planes.
"""

from __future__ import annotations

from typing import List, Literal, Optional, Union

from pydantic import Field

from .base import ConfigBase
from .types import Vector3Field


class PatchedShapeConfig(ConfigBase):
    """Configuration for patched sphere shapes (patched-sphere, sqrt-sphere, cube-sphere, se-sphere)."""

    type: Literal['patched-sphere', 'sqrt-sphere', 'cube-sphere', 'se-sphere'] = Field(description="Patched shape type")


class IcoSphereShapeConfig(ConfigBase):
    """Configuration for simple icosphere shape."""

    type: Literal['icosphere'] = Field(description="Simple shape type")
    subdivisions: Optional[int] = Field(3, description="Number of subdivisions for icosphere")


class SphereShapeConfig(ConfigBase):
    """Configuration for simple shpere shape."""

    type: Literal['sphere'] = Field(description="Sphere shape type")


class MeshShapeConfig(ConfigBase):
    """Configuration for mesh shapes."""

    type: Literal['mesh'] = 'mesh'
    model: str = Field(description="Mesh model file path")
    create_uv: bool = Field(False, description="Create UV coordinates")
    panda: bool = Field(False, description="Use Panda3D mesh format")
    auto_scale: bool = Field(False, description="Auto-scale mesh to radius")
    auto_center: bool = Field(False, description="Auto-center mesh")
    offset: Optional[Vector3Field] = Field(None, description="Mesh offset [x, y, z]")
    rotation: Optional[List[float]] = Field(None, description="Mesh rotation (HPR or quaternion)")
    scale: Optional[Union[float, List[float]]] = Field(None, description="Mesh scale factor or [x, y, z]")
    scale_units: Optional[str] = Field(None, description="Units for scale")
    flatten: bool = Field(True, description="Flatten mesh hierarchy")
    attribution: Optional[Union[str, List[str]]] = Field(None, description="Model attribution/source")


class BillboardShapeConfig(ConfigBase):
    """Configuration for billboard/raymarching shapes."""

    type: Literal['raymarching', 'billboard'] = Field(description="Billboard shape type")


class TiledPlaneShapeConfig(ConfigBase):
    """Configuration for tiled plane shapes."""

    type: Literal['tiled-plane'] = 'tiled-plane'
    tile_size: Optional[int] = Field(None, description="Tile size")
