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
Terrain populator configuration schemas.

Defines Pydantic models for terrain layer populators that scatter objects
(trees, rocks, etc.) across terrain surfaces.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import Field

from .base import ConfigBase


class PopulatorConfig(ConfigBase):
    """Configuration for a terrain object populator layer."""

    type: Optional[str] = Field(None, description="Populator implementation type ('cpu' or 'gpu')")
    density: float = Field(250.0, description="Object density (objects per km²)")
    max_instances: int = Field(1000, description="Maximum number of object instances")
    min_lod: int = Field(0, description="Minimum level of detail at which to show this layer")
    shape: Optional[Any] = Field(None, description="Shape configuration for the instanced objects")
    appearance: Optional[Any] = Field(None, description="Appearance configuration for the instanced objects")
    vertex: Optional[Any] = Field(None, description="Vertex shader control configuration")
    placer: Optional[Any] = Field(None, description="Object placement algorithm configuration")
