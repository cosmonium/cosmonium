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

from typing import Any, List, Optional

from pydantic import Field

from .base import ConfigBase


class CartesianWorldConfig(ConfigBase):
    """Configuration for a Cartesian (non-stellar) world."""

    name: Optional[str] = Field(None, description="World name")
    controller: Optional[Any] = Field(None, description="Movement controller configuration")
    entities: List[Any] = Field(default_factory=list, description="List of entity configurations")
    lights: List[Any] = Field(default_factory=list, description="List of local light configurations")
