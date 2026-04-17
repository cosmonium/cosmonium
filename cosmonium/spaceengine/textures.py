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

"""SpaceEngine virtual texture source and factory for cubemap-based textures.

Provides support for SpaceEngine's cubemap texture format, which stores textures
in per-face directories (pos_x, neg_x, pos_y, neg_y, pos_z, neg_z) with texture
files named using a ``LOD_Y_X[_channel].ext`` convention. Includes coordinate
mapping from Cosmonium's Z-up system to SpaceEngine's Y-up system.
"""

import os

from ..dircontext import defaultDirContext
from ..textures import AutoTextureSource, TextureSourceFactory, VirtualTextureSource


class SpaceEngineVirtualTextureSource(VirtualTextureSource):
    """Virtual texture source for SpaceEngine's cubemap texture format.

    Loads textures from per-face directories (pos_x, neg_x, pos_y, neg_y, pos_z,
    neg_z) where each texture is named ``{LOD}_{Y}_{X}[_{channel}].{ext}``.
    Supports separate color and alpha channels. Face indices are mapped from
    Cosmonium's Z-up coordinate system to SpaceEngine's Y-up coordinate system.
    """

    face_str = [
        # Cosmonium (Z-up) to SpaceEngine (Y-up) axis mapping:
        # Cosmonium X (right) -> SE X
        # Cosmonium Y (forward) -> SE -Z
        # Cosmonium Z (up) -> SE Y
        'pos_x',  # face 0 RIGHT (+X)
        'neg_x',  # face 1 LEFT (-X)
        'pos_z',  # face 2 BACK (-Y) -> SE +Z
        'neg_z',  # face 3 FRONT (+Y) -> SE -Z
        'pos_y',  # face 4 TOP (+Z) -> SE +Y
        'neg_y',  # face 5 BOTTOM (-Z) -> SE -Y
    ]

    def __init__(self, root, ext, size, channel=None, alpha_channel=None, attribution=None, context=defaultDirContext):
        VirtualTextureSource.__init__(self, root, ext, size, attribution, context)
        self.channel = channel
        self.alpha_channel = alpha_channel
        if channel is None:
            self.channel_text = ''
        else:
            self.channel_text = '_' + channel
        if self.alpha_channel is None:
            self.alpha_channel_text = ''
        else:
            self.alpha_channel_text = '_' + alpha_channel

    def child_texture_name(self, patch):
        """Return the file path for any next-higher-resolution child texture.

        Args:
            patch: The texture patch.

        Returns:
            Full path to a child texture at LOD+1 in the face directory.
        """
        dir_name = self.face_str[patch.face]
        x = patch.x
        y = (1 << patch.lod) - patch.y - 1
        return (
            self.root + '/' + dir_name + "/%d_%d_%d%s.%s" % (patch.lod + 1, y * 2, x * 2, self.channel_text, self.ext)
        )

    def texture_name(self, patch):
        """Return the file path for the texture at the patch's current LOD.

        Args:
            patch: The texture patch.

        Returns:
            Full path to the texture in the face directory.
        """
        dir_name = self.face_str[patch.face]
        x = patch.x
        y = (1 << patch.lod) - patch.y - 1
        return self.root + '/' + dir_name + "/%d_%d_%d%s.%s" % (patch.lod, y, x, self.channel_text, self.ext)

    def alpha_texture_name(self, patch):
        """Return the file path for the alpha channel texture, if configured.

        Args:
            patch: The texture patch containing face, x, y, and lod attributes.

        Returns:
            Full path to the alpha texture, or ``None`` if no alpha channel.
        """
        if self.alpha_channel is not None:
            dir_name = self.face_str[patch.face]
            x = patch.x
            y = (1 << patch.lod) - patch.y - 1
            return self.root + '/' + dir_name + "/%d_%d_%d%s.%s" % (patch.lod, y, x, self.alpha_channel_text, self.ext)

    def get_recommended_shape(self):
        """Return the recommended geometry shape for this texture source.

        Returns:
            The id of supported geometry shape: ``'sqrt-sphere'``.
        """
        return 'sqrt-sphere'


class SpaceEngineTextureSourceFactory(TextureSourceFactory):
    """Factory that creates virtual texture sources from SpaceEngine directories.

    Auto-detects SpaceEngine cubemap directory structures by checking for the
    presence of all six face subdirectories. Also detects channel configurations
    (color ``_c`` and alpha ``_a`` suffixes) from base texture naming conventions.
    """

    def create_source(self, filename, context=defaultDirContext):
        """Detect and create a SpaceEngine virtual texture source.

        Resolves the filename via the directory context, verifies that all six
        cubemap face subdirectories exist, and detects channel suffixes from
        the base texture files.

        Args:
            filename: Path to the SpaceEngine texture directory.
            context: Directory context for resolving file paths.

        Returns:
            A ``SpaceEngineVirtualTextureSource`` if the directory is a valid
            SpaceEngine cubemap, or ``None`` otherwise.
        """
        filename = context.find_texture(filename)
        if filename is None:
            return None
        if os.path.isdir(filename):
            all_faces = True
            for face in SpaceEngineVirtualTextureSource.face_str:
                if not os.path.isdir(os.path.join(filename, face)):
                    all_faces = False
            if all_faces:
                channel = None
                alpha_channel = None
                # Check if textures are in separate channels or not.
                # If not, the alpha channel is assumed to be in the same file as the color channel.
                if not os.path.exists(os.path.join(filename, 'base.jpg')):
                    if os.path.exists(os.path.join(filename, 'base_c.jpg')):
                        channel = 'c'
                    if os.path.exists(os.path.join(filename, 'base_a.jpg')):
                        alpha_channel = 'a'
                return SpaceEngineVirtualTextureSource(filename, 'jpg', 258, channel, alpha_channel)
        return None


# TODO: Should be done in Cosmonium main class
AutoTextureSource.register_source_factory(SpaceEngineTextureSourceFactory(), [], 1)
