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
Texture configuration schemas.

Defines Pydantic models for texture sources and configurations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field

from .base import ConfigBase


class TextureDictionaryEntryConfig(ConfigBase):
    """Configuration for a texture dictionary entry."""

    albedo: Optional[Any] = Field(None, description="Albedo texture configuration")
    normal: Optional[Any] = Field(None, description="Normal map configuration")
    occlusion: Optional[Any] = Field(None, description="Occlusion map configuration")


class TextureDictionaryConfig(ConfigBase):
    """Configuration for texture dictionaries."""

    srgb: Optional[bool] = Field(None, description="Use sRGB color space")
    entries: Dict[str, Any] = Field(default_factory=dict, description="Dictionary entries")
    scale: Optional[float | List[float]] = Field(None, description="Texture scale")
    tiling: Optional[Any] = Field(None, description="Tiling configuration")
