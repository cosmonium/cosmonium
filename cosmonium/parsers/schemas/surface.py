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
Surface configuration schemas.

Defines Pydantic models for surface appearance, shape, and complete surface configuration.
"""

from __future__ import annotations

from typing import Literal, Optional, Union

from pydantic import Field

from .base import ConfigBase
from .types import Vector3Field


class SurfaceConfig(ConfigBase):
    """Complete surface configuration including category, appearance, shape, and lighting."""

    name: Optional[str] = Field(None, description="Surface name")
    category: Optional[str] = Field('visible', description="Surface category")

    # Surface properties
    radius: Optional[float] = Field(None, description="Surface radius")
    oblateness: Optional[float] = Field(None, description="Surface oblateness/ellipticity")
    scale: Optional[Vector3Field] = Field(None, description="Surface scale [x, y, z]")

    # Nested configurations - can be references (strings) or inline dicts
    appearance: Optional[Union[str, dict]] = Field(None, description="Appearance configuration or reference")
    shape: Optional[Union[str, dict]] = Field(None, description="Shape configuration or reference")
    heightmap: Optional[Union[str, dict]] = Field(None, description="Heightmap configuration or reference")

    # Lighting
    lighting_model: Optional[str] = Field(None, description="Lighting model name")

    # Metadata
    resolution: Optional[float] = Field(None, description="Surface resolution")
    attribution: Optional[str] = Field(None, description="Data attribution/source")
    source: Optional[str] = Field(None, description="Data source (alias for attribution)")


class SurfaceCategoryConfig(ConfigBase):
    """Configuration for surface category."""

    type: Literal['surface-category'] = Field(default='surface-category', description="Object type")
    name: str = Field(..., description="Category name")
