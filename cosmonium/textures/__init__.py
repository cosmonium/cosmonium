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

"""Core texture management.

This package separates texture *sources* (how texture data is
obtained) from texture *wrappers* (how textures are configured and applied
to scene geometry).

Sub-modules
-----------
config
    :class:`TexCoord` and :class:`TextureConfiguration`.
base
    Abstract base classes :class:`TextureBase` and :class:`TextureSource`.
sources
    Concrete texture source implementations (file-based, virtual/patched, etc.).
types
    Concrete texture wrapper types (surface, normal map, specular map, etc.).
"""

from .base import TextureBase, TextureSource
from .config import TexCoord, TextureConfiguration
from .sources import (
    AutoTextureSource,
    DirectTextureSource,
    InvalidTextureSource,
    TextureFileSource,
    TextureFileSourceFactory,
    TextureSourceFactory,
    VirtualTextureSource,
)
from .types import (
    BumpMapTexture,
    DataTexture,
    EmissionTexture,
    HeightMapTexture,
    NormalMapTexture,
    OcclusionMapTexture,
    SimpleTexture,
    SpecularMapTexture,
    SurfaceTexture,
    TextureArray,
    TransparentTexture,
    VisibleTexture,
    WrapperTexture,
)

__all__ = [
    'TexCoord',
    'TextureConfiguration',
    'TextureBase',
    'TextureSource',
    'InvalidTextureSource',
    'AutoTextureSource',
    'TextureSourceFactory',
    'TextureFileSource',
    'TextureFileSourceFactory',
    'DirectTextureSource',
    'VirtualTextureSource',
    'WrapperTexture',
    'SimpleTexture',
    'DataTexture',
    'VisibleTexture',
    'SurfaceTexture',
    'EmissionTexture',
    'TransparentTexture',
    'NormalMapTexture',
    'SpecularMapTexture',
    'OcclusionMapTexture',
    'BumpMapTexture',
    'TextureArray',
    'HeightMapTexture',
]
