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

"""Procedural virtual texture sources.

:class:`ProceduralVirtualTextureSource` generates a single texture for the
whole surface and caches it.
:class:`PatchedProceduralVirtualTextureSource` generates one texture per
terrain patch, with ancestor fallback when a patch has not yet been generated.
"""

import logging

from direct.showbase.ShowBaseGlobal import globalClock

from ... import settings
from ...textures import TextureSource

logger = logging.getLogger("textures")


class ProceduralVirtualTextureSource(TextureSource):
    """Texture source that generates a single procedural texture.

    Produces one texture for the entire surface on first load and caches the
    result. Suitable for non-patched bodies where a single texture covers
    the whole object.
    """

    cached = True
    procedural = True

    def __init__(self, tex_generator, size):
        """Initialize the procedural virtual texture source.

        Args:
            tex_generator: Generator used to produce the procedural texture.
            size: Square texture size in pixels (width and height).
        """
        TextureSource.__init__(self)
        self.texture_size = size
        self.tex_generator = tex_generator

    async def load(self, tasks_tree, shape, texture_config):
        """Load the procedural texture, generating it if not yet cached.

        Args:
            tasks_tree: Task tree for managing asynchronous dependencies.
            shape: The shape object that owns the texture.
            texture_config: Configuration for the output color texture.

        Returns:
            tuple: (texture, texture_size, lod) where lod is always 0.
        """
        if self.texture is None:
            self.texture = await self.tex_generator.generate(tasks_tree, shape, None, texture_config)
        return (self.texture, self.texture_size, 0)

    def get_texture(self, shape, strict=False):
        """Return the cached texture tuple.

        Args:
            shape: The shape requesting the texture.
            strict: Unused; present for interface compatibility.

        Returns:
            tuple: (texture, texture_size, lod) where lod is always 0.
        """
        return (self.texture, self.texture_size, 0)

    def clear_all(self):
        """Release the cached texture and the underlying generator."""
        self.texture = None
        self.tex_generator.clear_all()


class PatchedProceduralVirtualTextureSource(TextureSource):
    """Patched texture source that generates a procedural texture per patch.

    Maintains a cache of generated textures keyed by patch ID. Each patch
    gets its own texture at the appropriate level of detail. When a patch
    texture is not yet available, the nearest ancestor texture is returned
    as a fallback.
    """

    cached = False

    def __init__(self, tex_generator, size):
        """Initialize the patched procedural virtual texture source.

        Args:
            tex_generator: Generator used to produce per-patch textures.
            size: Square texture size in pixels (width and height).
        """
        TextureSource.__init__(self)
        self.texture_size = size
        self.map_patch = {}
        self.tex_generator = tex_generator
        self.procedural = True

    def add_as_source(self, shape):
        """Register the generator's texture source on the given shape.

        Args:
            shape: The shape to add the texture source to.
        """
        self.tex_generator.add_as_source(shape)

    def is_patched(self):
        return True

    def child_texture_name(self, patch):
        return None

    def texture_name(self, patch):
        return None

    def can_split(self, patch):
        return True

    async def load(self, tasks_tree, patch, texture_config):
        """Load or generate the texture for a specific patch.

        Returns a cached result if the patch has already been generated,
        otherwise triggers generation and caches the result.

        Args:
            tasks_tree: Task tree for managing asynchronous dependencies.
            patch: The patch to generate the texture for.
            texture_config: Configuration for the output color texture.

        Returns:
            tuple: (texture, texture_size, lod) for the requested patch.
        """
        if settings.debug_tex_loading:
            logger.debug(f"{globalClock.get_frame_count()} Loading texture for {patch.str_id()}")
        texture_info = None
        if not patch.str_id() in self.map_patch:
            texture = await self.tex_generator.generate(tasks_tree, patch.owner, patch, texture_config)
            if settings.debug_tex_loading:
                logger.debug(f"{globalClock.get_frame_count()} Texture ready for {patch.str_id()}")
            texture_info = (texture, self.texture_size, patch.lod)
            self.map_patch[patch.str_id()] = texture_info
        else:
            texture_info = self.map_patch[patch.str_id()]
        return texture_info

    def clear(self, patch):
        """Remove the cached texture for a specific patch.

        Args:
            patch: The patch whose cached texture should be removed.
        """
        try:
            del self.map_patch[patch.str_id()]
        except KeyError:
            pass

    def clear_all(self):
        """Release all cached patch textures and the underlying generator."""
        self.map_patch = {}
        self.tex_generator.clear_all()

    def get_texture(self, patch, strict=False):
        """Retrieve the texture for a patch, with optional ancestor fallback.

        Args:
            patch: The patch to retrieve the texture for.
            strict: If True, return None when the exact patch texture is
                missing. If False, walk up the parent chain to find the
                nearest available ancestor texture.

        Returns:
            tuple: (texture, texture_size, lod) for the patch or its nearest
                ancestor, or (None, texture_size, lod) if unavailable.
        """
        if patch.str_id() in self.map_patch:
            return self.map_patch[patch.str_id()]
        elif not strict:
            parent_patch = patch.parent
            while parent_patch is not None and parent_patch.str_id() not in self.map_patch:
                parent_patch = parent_patch.parent
            if parent_patch is not None:
                if settings.debug_tex_loading:
                    logger.debug(
                        f"{globalClock.get_frame_count()} Using parent texture for {patch.str_id()},"
                        f" parent: {parent_patch.str_id()}"
                    )
                return self.map_patch[parent_patch.str_id()]
            else:
                if settings.debug_tex_loading:
                    logger.debug(f"{globalClock.get_frame_count()} No texture found for {patch.str_id()}")
                return (None, self.texture_size, patch.lod)
        else:
            return (None, self.texture_size, patch.lod)
