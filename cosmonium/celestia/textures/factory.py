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

"""Celestia virtual texture factory for .ctx virtual texture files.

Provides the ``CelestiaVirtualTextureSourceFactory`` class which delegates
parsing of ``.ctx`` files to the ``ctx_parser`` module.
"""

from ...textures import TextureSourceFactory
from .. import ctx_parser


class CelestiaVirtualTextureSourceFactory(TextureSourceFactory):
    """Factory that creates virtual texture sources from Celestia .ctx files.

    Delegates parsing of ``.ctx`` files to the ``ctx_parser`` module to produce
    a configured ``CelestiaVirtualTextureSource`` instance.
    """

    def create_source(self, filename, context=None):
        """Parse a .ctx file and return the corresponding texture source.

        Args:
            filename: Path to the ``.ctx`` virtual texture definition file.
            context: Directory context for resolving file paths.

        Returns:
            A ``CelestiaVirtualTextureSource`` configured from the .ctx file.
        """
        return ctx_parser.parse_file(filename, context)
