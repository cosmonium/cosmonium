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

"""Celestia virtual texture source for .ctx virtual texture files.

Provides the ``CelestiaVirtualTextureSource`` class which handles the
level-based directory hierarchy (level0/, level1/, etc.) with texture files
named using a ``tx_X_Y.ext`` convention.
"""

import os

from ...textures import VirtualTextureSource


class CelestiaVirtualTextureSource(VirtualTextureSource):
    """Virtual texture source for Celestia's .ctx virtual texture format.

    Loads textures from a level-based directory hierarchy where each LOD level
    is stored in a separate directory (level0/, level1/, etc.) and textures are
    named ``{prefix}{X}_{Y}.{ext}``. Supports an optional longitude offset
    for repositioning the texture origin.
    """

    def __init__(self, root, ext, size, prefix='tx_', offset=0, context=None):
        VirtualTextureSource.__init__(self, root, ext, size, context)
        self.prefix = prefix
        self.offset = offset

    def set_offset(self, offset):
        """Set the longitude offset for texture coordinates.

        Args:
            offset: Longitude offset value. When non-zero, texture X coordinates
                are shifted by half the subdivision count at the current LOD.
                Y offset is ignored as not supported by Celestia's texture format.
        """
        self.offset = offset

    def get_patch_name(self, patch, scale=1):
        """Build the texture filename for a given patch.

        Args:
            patch: The texture patch containing x, y, and lod attributes.
            scale: Coordinate multiplier, typically 2 for child textures.
        Returns:
            Texture filename string in the format ``{prefix}{X}_{Y}.{ext}``.
        """
        x = patch.x
        y = (1 << patch.lod) - patch.y - 1
        if self.offset != 0:
            s_div = 2 << patch.lod
            x += s_div // 2
            x %= s_div
        return "%s%d_%d.%s" % (self.prefix, x * scale, y * scale, self.ext)

    def child_texture_name(self, patch):
        """Return the file path for the next-higher-resolution child texture.

        Args:
            patch: The texture patch to resolve.

        Returns:
            Full path to the child texture at ``level{lod+1}/``.
        """
        return os.path.join(self.root, 'level%d' % (patch.lod + 1), self.get_patch_name(patch, 2))

    def texture_name(self, patch):
        """Return the file path for the texture at the patch's current LOD.

        Args:
            patch: The texture patch to resolve.

        Returns:
            Full path to the tile at ``level{lod}/``.
        """
        return os.path.join(self.root, 'level%d' % patch.lod, self.get_patch_name(patch))

    def alpha_texture_name(self, patch) -> str | None:
        # Separate alpha textures are not supported by Celestia.
        return None

    def get_recommended_shape(self):
        """Return the recommended geometry shape for this texture source.

        Returns:
            Celestia virtual textures supports only ``'patched-sphere'`` (UV Sphere).
        """
        return 'patched-sphere'
