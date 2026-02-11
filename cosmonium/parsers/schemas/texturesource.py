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

from typing import Any, Literal, Optional

from pydantic import Field

from .base import ConfigBase


class TextureFileSourceConfig(ConfigBase):
    """Configuration for file-based texture sources."""

    type: Literal['file'] = 'file'
    name: Optional[str] = Field(None, description="Texture name")
    file: str = Field(..., description="Texture file path")
    offset: int = Field(0, description="Texture offset")
    attribution: Optional[str] = Field(None, description="Texture attribution/source")


class CelestiaVirtualTextureSourceConfig(ConfigBase):
    """Configuration for Celestia virtual texture sources."""

    type: Literal['ctx'] = 'ctx'
    name: Optional[str] = Field(None, description="Texture name")
    root: str = Field(..., description="Root directory for texture tiles")
    ext: str = Field('dds', description="Texture file extension")
    size: Optional[int] = Field(None, description="Texture tile size")
    prefix: str = Field('tx_', description="Texture file prefix")
    offset: int = Field(0, description="Texture offset")
    attribution: Optional[str] = Field(None, description="Texture attribution/source")


class SpaceEngineVirtualTextureSourceConfig(ConfigBase):
    """Configuration for SpaceEngine virtual texture sources."""

    type: Literal['se'] = 'se'
    name: Optional[str] = Field(None, description="Texture name")
    root: str = Field(..., description="Root directory for texture tiles")
    ext: str = Field('jpg', description="Texture file extension")
    size: int = Field(258, description="Texture tile size")
    color: Optional[str] = Field(None, description="Color channel")
    alpha: Optional[str] = Field(None, description="Alpha channel")
    attribution: Optional[str] = Field(None, description="Texture attribution/source")


class ProceduralTextureSourceConfig(ConfigBase):
    """Configuration for procedural texture sources."""

    type: Literal['procedural'] = 'procedural'
    name: Optional[str] = Field(None, description="Texture name")
    func: Optional[Any] = Field(None, description="Noise function configuration")
    noise: Optional[Any] = Field(None, description="Noise function (deprecated, use func)")
    target: str = Field('gray', description="Target channel (gray, alpha, color, normal)")
    size: int = Field(256, description="Texture size")


class ReferenceTextureSourceConfig(ConfigBase):
    """Configuration for reference texture sources."""

    type: Literal['ref'] = 'ref'
    ref: str = Field(..., description="Reference name")
