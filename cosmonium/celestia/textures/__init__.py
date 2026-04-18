#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
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

"""Celestia virtual texture source and factory for .ctx virtual texture files.

Provides support for Celestia's virtual texture format, which organizes textures
in a level-based directory hierarchy (level0/, level1/, etc.) with texture files
named using a ``tx_X_Y.ext`` convention.
"""

from ...textures import AutoTextureSource
from .factory import CelestiaVirtualTextureSourceFactory
from .source import CelestiaVirtualTextureSource

__all__ = ['CelestiaVirtualTextureSource', 'CelestiaVirtualTextureSourceFactory']


def init():
    AutoTextureSource.register_source_factory(CelestiaVirtualTextureSourceFactory(), ['ctx'], 0)
