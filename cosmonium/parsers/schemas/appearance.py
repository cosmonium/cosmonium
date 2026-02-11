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
Appearance configuration schemas.

Defines Pydantic models for different appearance types including textures,
model, procedural, and deferred procedural appearances.
"""

from __future__ import annotations

from typing import Any, List, Literal, Optional

from pydantic import Field

from .base import ConfigBase


class TexturesAppearanceConfig(ConfigBase):
    """Configuration for texture-based appearances."""

    type: Literal['textures'] = 'textures'
    texture: Optional[Any] = Field(None, description="Main texture configuration or path")
    tint: Optional[List[float]] = Field(None, description="Tint color [r, g, b, a]")
    transparency: bool = Field(False, description="Enable transparency")
    transparency_level: float = Field(0.0, description="Transparency level")
    transparency_blend: Optional[str] = Field(None, description="Transparency blend mode")

    night_texture: Optional[Any] = Field(None, description="Night/emission texture")
    emission_texture: Optional[Any] = Field(None, description="Emission texture")
    nightscale: float = Field(0.02, description="Night texture scale factor")

    normalmap: Optional[Any] = Field(None, description="Normal map configuration")
    specular_color: Optional[List[float]] = Field(None, description="Specular color [r, g, b]")
    shininess: float = Field(1.0, description="Shininess factor")
    specularmap: Optional[Any] = Field(None, description="Specular map configuration")

    bumpmap: Optional[Any] = Field(None, description="Bump map configuration")
    bump_height: float = Field(0.0, description="Bump map height")

    diffuse_color: Optional[List[float]] = Field(None, description="Diffuse color [r, g, b, a]")
    emission_color: Optional[List[float]] = Field(None, description="Emission color [r, g, b, a]")

    roughness: float = Field(0.0, description="Surface roughness")
    backlit: Optional[float] = Field(None, description="Enable backlighting")
    attribution: Optional[str] = Field(None, description="Texture attribution/source")

    # Shadow bias parameters
    normal_bias: Optional[float] = Field(None, description="Shadow normal bias")
    slope_bias: Optional[float] = Field(None, description="Shadow slope bias")
    depth_bias: Optional[float] = Field(None, description="Shadow depth bias")


class ModelAppearanceConfig(ConfigBase):
    """Configuration for model appearances."""

    type: Literal['model'] = 'model'
    material: bool = Field(True, description="Use model materials")
    vertex_color: bool = Field(True, description="Use vertex colors")
    occlusion_channel: bool = Field(False, description="Use occlusion channel")

    # Shadow bias parameters
    normal_bias: Optional[float] = Field(None, description="Shadow normal bias")
    slope_bias: Optional[float] = Field(None, description="Shadow slope bias")
    depth_bias: Optional[float] = Field(None, description="Shadow depth bias")


class ProceduralAppearanceConfig(ConfigBase):
    """Configuration for procedural appearances."""

    type: Literal['procedural'] = 'procedural'
    control: Optional[Any] = Field(None, description="Texture control configuration")
    textures: Optional[Any] = Field(None, description="Texture dictionary configuration")


class DeferredProceduralAppearanceConfig(ConfigBase):
    """Configuration for deferred procedural appearances."""

    type: Literal['deferred-procedural'] = 'deferred-procedural'
    control: Optional[Any] = Field(None, description="Texture control configuration")
    textures: Optional[Any] = Field(None, description="Texture dictionary configuration")
    size: int = Field(256, description="Texture generation size")
