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
World configuration schemas.

Defines Pydantic models for Cartesian world configurations.
"""

from __future__ import annotations

from typing import Any, List, Optional, Union

from pydantic import Field

from .base import ConfigBase


class CartesianWorldConfig(ConfigBase):
    """Configuration for a Cartesian (non-stellar) world."""

    name: Optional[str] = Field(None, description="World name")
    controller: Optional[Any] = Field(None, description="Movement controller configuration")
    entities: List[Any] = Field(default_factory=list, description="List of entity configurations")
    lights: List[Any] = Field(default_factory=list, description="List of local light configurations")


class FlatTerrainWorldConfig(ConfigBase):
    """Configuration for a flat terrain world."""

    tile_size: int = Field(1024, description="Tile size in meters")
    max_vertex_size: int = Field(128, description="Maximum vertex count per patch edge")
    max_lod: int = Field(10, description="Maximum LOD level")
    max_distance: Optional[float] = Field(None, description="Maximum visibility distance")
    tile_density: Optional[float] = Field(None, description="Tile density")
    hw_tessellation: bool = Field(False, description="Hardware tessellation enabled")
    shape: Optional[Any] = Field(None, description="Shape configuration")
    appearance: Optional[Union[str, dict, Any]] = Field(None, description="Appearance")
    lighting_model: Optional[str] = Field(None, description="Lighting model name")
    heightmap: Optional[Union[str, dict, Any]] = Field(None, description="Heightmap")
    biome: Optional[Union[str, dict, Any]] = Field(None, description="Biome heightmap")
    layers: List[Any] = Field(default_factory=list, description="Populator layers")


class FlatUniverseConfig(ConfigBase):
    """Configuration for a flat (non-stellar) universe."""

    terrain: Optional[Any] = Field(None, description="Terrain configuration")
    lights: List[Any] = Field(default_factory=list, description="Light configurations")
    scattering: Optional[Any] = Field(None, description="Scattering configuration")
    worlds: List[Any] = Field(default_factory=list, description="World configurations")
