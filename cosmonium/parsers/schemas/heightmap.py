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
Heightmap configuration schemas.

Defines Pydantic models for heightmaps with noise configuration.
"""

from typing import Any, Optional

from pydantic import ConfigDict, Field

from .base import ConfigBase
from .types import DistanceMField


class HeightmapConfig(ConfigBase):
    """Configuration for heightmaps with noise."""

    name: Optional[str] = Field(None, description="Heightmap name")

    # Height parameters
    min_height: Optional[DistanceMField] = Field(None, description="Minimum height (float in m, or [value, unit])")
    max_height: Optional[DistanceMField] = Field(None, description="Maximum height (float in m, or [value, unit])")
    height_scale: DistanceMField = Field(1.0, description="Height scale factor (float in m, or [value, unit])")
    height_offset: DistanceMField = Field(0.0, description="Height offset (float in m, or [value, unit])")
    scale_length: Optional[DistanceMField] = Field(None, description="Scale length (float in m, or [value, unit])")

    # Noise/procedural configuration
    func: Optional[dict] = Field(None, description="Noise function configuration")
    noise: Optional[dict] = Field(None, description="Noise function configuration (Deprecated alias for func)")

    # Texture configuration
    data: Optional[Any] = Field(None, description="Texture data source")
    size: Optional[int] = Field(256, description="Heightmap texture size")
    overlap: int = Field(1, description="Tile overlap for patched heightmaps")

    # Interpolation and filtering
    interpolator: Optional[Any] = Field(None, description="Interpolator configuration")
    filter: Optional[Any] = Field(None, description="Filter configuration")

    # LOD control
    max_lod: int = Field(100, description="Maximum level of detail")


class StandaloneHeightmapConfig(ConfigBase):
    """Configuration for standalone heightmap.

    Heightmap specific parameters are not specified, all extra parameters are forwarded
    to the appropriate heightmap sub-parser.
    """

    model_config = ConfigDict(extra='allow')  # Allow extra fields for heightmap-specific parameters
    name: str = Field(..., description="Name to register in the heightmap database")
