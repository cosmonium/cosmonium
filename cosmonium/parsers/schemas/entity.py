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
Entity configuration schemas.

Defines Pydantic models for scene entities (visible objects in Cartesian worlds).
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import Field

from .base import ConfigBase


class EntityConfig(ConfigBase):
    """Configuration for a scene entity."""

    name: Optional[str] = Field(None, description="Entity name")
    disabled: bool = Field(False, description="Whether the entity is disabled")
    shape: Optional[Any] = Field(None, description="Shape configuration")
    appearance: Optional[Any] = Field(None, description="Appearance configuration")
    lighting_model: Optional[Any] = Field(None, description="Lighting model configuration")
    physics: Optional[Any] = Field(None, description="Physics shape configuration")
