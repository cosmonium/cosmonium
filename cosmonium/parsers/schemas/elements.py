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
Body element configuration schemas.

Defines Pydantic models for body elements such as rings and clouds.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import Field

from .base import ConfigBase


class RingsConfig(ConfigBase):
    """Configuration for planetary rings."""

    inner_radius: Optional[float] = Field(None, description="Inner radius of the rings")
    outer_radius: Optional[float] = Field(None, description="Outer radius of the rings")
    lighting_model: Optional[Any] = Field(None, description="Lighting model configuration")
    appearance: Optional[Any] = Field(None, description="Appearance configuration")


class CloudsConfig(ConfigBase):
    """Configuration for cloud layers."""

    height: float = Field(0.0, description="Height of the cloud layer above the surface")
    shape: Optional[Any] = Field(None, description="Shape configuration")
    appearance: Optional[Any] = Field(None, description="Appearance configuration")
