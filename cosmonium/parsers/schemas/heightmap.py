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

from pydantic import Field

from .base import ConfigBase


class HeightmapConfig(ConfigBase):
    """Configuration for heightmaps with noise."""

    name: Optional[str] = Field(None, description="Heightmap name")

    # Height parameters
    min_height: Optional[float] = Field(None, description="Minimum height")
    max_height: Optional[float] = Field(None, description="Maximum height")
    height_scale: Optional[float] = Field(1.0, description="Height scale factor")
    height_offset: Optional[float] = Field(0.0, description="Height offset")
    scale_length: Optional[float] = Field(None, description="Scale length")

    # Units
    min_height_units: Optional[str] = Field('m', description="Units for min height")
    max_height_units: Optional[str] = Field('m', description="Units for max height")
    height_scale_units: Optional[str] = Field('m', description="Units for height scale")
    height_offset_units: Optional[str] = Field('m', description="Units for height offset")
    scale_length_units: Optional[str] = Field('m', description="Units for scale length")

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
