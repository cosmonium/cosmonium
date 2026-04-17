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

"""Procedural texture generation framework using GPU shader pipelines.

This package provides pipeline stages and generators for creating textures
procedurally via noise-based shaders and detail map composition. It supports
both single-shot texture generation for non-patched bodies and per-patch
level-of-detail generation for patched terrain surfaces. Textures are
rendered off-screen using process pipelines.

Sub-modules
-----------
stages
    :class:`TextureGenerationStage` and :class:`DetailTextureGenerationStage`.
generators
    :class:`NoiseTextureGenerator` and :class:`DetailMapTextureGenerator`.
sources
    :class:`ProceduralVirtualTextureSource` and
    :class:`PatchedProceduralVirtualTextureSource`.
"""

from .generators import DetailMapTextureGenerator, NoiseTextureGenerator
from .sources import PatchedProceduralVirtualTextureSource, ProceduralVirtualTextureSource
from .stages import DetailTextureGenerationStage, TextureGenerationStage

__all__ = [
    'TextureGenerationStage',
    'DetailTextureGenerationStage',
    'NoiseTextureGenerator',
    'DetailMapTextureGenerator',
    'ProceduralVirtualTextureSource',
    'PatchedProceduralVirtualTextureSource',
]
