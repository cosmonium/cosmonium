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
Annotations configuration schemas.

Defines Pydantic models for constellations and asterisms.
"""

from __future__ import annotations

from typing import Any, List, Literal, Optional, Union

from pydantic import Field

from .base import ConfigBase


class ConstellationConfig(ConfigBase):
    """Configuration for constellations."""

    type: Literal['constellation'] = Field(default='constellation', description="Object type")
    name: Union[str, List[str]] = Field(..., description="Constellation name(s)")
    abbreviation: Optional[str] = Field(None, description="IAU abbreviation")

    # Center position (for labeling)
    ra: str = Field(description="Right ascension in hours:minutes:seconds")
    de: str = Field(description="Declination in hours:minutes:seconds")

    # Boundaries and asterisms
    boundaries: Optional[Any] = Field(None, description="Constellation boundary data")


class AsterismConfig(ConfigBase):
    """Configuration for asterism (star pattern) segments."""

    type: Literal['asterism'] = Field(default='asterism', description="Object type")
    name: str = Field(description="Asterism name")

    # Segment data
    segments: Optional[List[List[str]]] = Field(
        default_factory=list, description="Star segment data [[hip1, hip2], ...]"
    )
    stars: Optional[List[str]] = Field(default_factory=list, description="Star identifiers")
