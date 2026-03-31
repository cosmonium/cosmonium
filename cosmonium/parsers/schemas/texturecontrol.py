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


"""Texture control configuration schemas."""

from __future__ import annotations

from typing import Any, List, Literal, Optional

from pydantic import Field

from .base import ConfigBase


class HeightLayerConfig(ConfigBase):
    """Configuration for a single height colormap layer."""

    height: float = Field(0.0, description="Height value")
    height_units: Optional[str] = Field(None, description="Height units")
    bottom: Optional[Any] = Field(None, description="Bottom color [r, g, b]")
    top: Any = Field(default_factory=lambda: [0, 0, 0], description="Top color [r, g, b]")


class HeightColorControlConfig(ConfigBase):
    """Configuration for height-based colormap texture control."""

    type: Literal['colormap'] = 'colormap'
    entries: List[HeightLayerConfig] = Field(default_factory=list, description="Height colormap entries")
    percentage: bool = Field(False, description="Whether heights are percentages")
    float_values: bool = Field(
        False, description="Whether color values are floats (0-1) or integers (0-255)", alias='float'
    )


class HeightTextureEntryConfig(ConfigBase):
    """Configuration for a height-based texture entry."""

    entry: Any = Field(None, description="Texture entry (string name or nested control)")
    height: float = Field(0.0, description="Height threshold")
    height_units: Optional[str] = Field(None, description="Height units")
    blend: float = Field(0.0, description="Blend distance")


class SlopeTextureEntryConfig(ConfigBase):
    """Configuration for a slope-based texture entry."""

    entry: Any = Field(None, description="Texture entry (string name or nested control)")
    angle: float = Field(0.0, description="Slope angle in degrees")
    blend: float = Field(0.0, description="Blend angle in degrees")


class BiomeTextureEntryConfig(ConfigBase):
    """Configuration for a biome-based texture entry."""

    entry: Any = Field(None, description="Texture entry (string name or nested control)")
    value: float = Field(0.0, description="Biome value")
    blend: float = Field(1.0, description="Blend amount")


class MixTextureControlConfig(ConfigBase):
    """Configuration for mixed texture control."""

    type: Literal['textures'] = 'textures'
    height: Optional[List[HeightTextureEntryConfig]] = Field(None, description="Height-based control entries")
    slope: Optional[List[SlopeTextureEntryConfig]] = Field(None, description="Slope-based control entries")
    biome: Optional[List[BiomeTextureEntryConfig]] = Field(None, description="Biome-based control entries")
    entry: Optional[Any] = Field(None, description="Direct entry (string or nested)")
