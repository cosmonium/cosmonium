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

"""Concrete texture source implementations.

Provides file-based, factory-dispatching, direct-object, and virtual
(patched LOD) texture sources, together with the factory base class and
the fallback factory registration.
"""

import logging
import os

from .. import settings, workers
from .base import TextureSource

logger = logging.getLogger("textures")


class InvalidTextureSource(TextureSource):
    """Null texture source returned when no valid source can be resolved."""

    async def load(self, tasks_tree, patch, texture_config=None):
        return (None, 0, 0)


class AutoTextureSource(TextureSource):
    """Factory-dispatching texture source that selects a loader by file extension.

    Iterates through registered ``TextureSourceFactory`` instances (ordered by
    priority) and delegates to the first factory that can handle the given
    filename. Falls back to ``InvalidTextureSource`` if no factory matches.
    """

    factories = []

    def __init__(self, filename, attribution=None, context=None):
        """Initialize the auto texture source with the given filename and context.
        Args:
            filename: The file path or identifier for the texture to load.
            attribution: Optional attribution string for the texture source.
            context: Directory context for resolving texture file paths.
        """
        TextureSource.__init__(self, attribution)
        assert context is not None, "Context is required for AutoTextureSource"
        self.filename = filename
        self.context = context
        self.source = None
        # TODO: override as these are accessed directly by external classes :(
        # should be transformed into methods
        self.cached = True

    @classmethod
    def register_source_factory(cls, factory, extensions, priority):
        """Register a texture source factory for the given file extensions.

        Args:
            factory: A ``TextureSourceFactory`` instance.
            extensions: List of file extensions this factory handles (empty
                list means it handles all extensions).
            priority: Lower values are tried first.
        """
        # TODO: use struct iso tuple
        entry = (factory, extensions, priority)
        cls.factories.append(entry)
        cls.factories.sort(key=lambda x: x[2])

    def create_source(self):
        """Resolve and instantiate the concrete texture source via registered factories."""
        filename = self.filename
        if filename.endswith('.*'):
            filename = self.context.find_texture(filename)
            if filename is None:
                logger.error(f"Could not find {self.filename}")
                self.source = InvalidTextureSource()
                return
        base, extension = os.path.splitext(filename)
        if len(extension) > 0:
            extension = extension[1:]
        for entry in self.factories:
            if len(entry[1]) == 0 or extension in entry[1]:
                self.source = entry[0].create_source(self.filename, self.context)
                if self.source is not None:
                    self.cached = self.source.cached
                    self.texture_size = self.source.texture_size
                    return
        logger.error(f"Could not find loader for {self.filename}")
        self.source = InvalidTextureSource()

    def is_patched(self):
        """Return True if the resolved texture source is a patched (virtual) texture."""
        if self.source is None:
            self.create_source()
        return self.source.is_patched()

    def texture_name(self, patch):
        """Return the filename or identifier for the texture corresponding to the given patch, if applicable."""
        return self.filename

    def texture_filename(self, patch):
        """Return the resolved filename for the texture corresponding to the given patch, if applicable."""
        if self.source is None:
            self.create_source()
        return self.source.texture_filename(patch)

    def set_offset(self, offset):
        """Set the UV offset for the textures, if applicable."""
        if self.source is None:
            self.create_source()
        self.source.set_offset(offset)

    def load(self, tasks_tree, patch, texture_config=None):
        """Load the texture data for the given patch if not already loaded, delegating to the resolved source."""
        if self.source is None:
            self.create_source()
        return self.source.load(tasks_tree, patch, texture_config)

    def clear(self, patch):
        """Unload or clear the texture data for a specific patch, delegating to the resolved source."""
        if self.source is None:
            self.create_source()
        self.source.clear(patch)

    def clear_all(self):
        """Clear all texture data managed by this wrapper, delegating to the resolved source."""
        if self.source is None:
            self.create_source()
        self.source.clear_all()

    def can_split(self, patch):
        """Return True if this texture can be split into higher-resolution textures for the given patch,
        delegating to the resolved source."""
        if self.source is None:
            self.create_source()
        return self.source.can_split(patch)

    def get_texture(self, patch):
        """Return the texture for the given patch, or a default texture if not available,
        delegating to the resolved source."""
        if self.source is None:
            self.create_source()
        return self.source.get_texture(patch)

    def get_recommended_shape(self):
        """Return the recommended shape for this texture, if applicable,
        delegating to the resolved source."""
        if self.source is None:
            self.create_source()
        return self.source.get_recommended_shape()


class TextureSourceFactory:
    """Base factory for creating ``TextureSource`` instances from a filename.

    Subclasses override ``create_source`` to return the appropriate
    ``TextureSource`` for a given file path and directory context.
    """

    def create_source(self, filename, context=None):
        return None


class TextureFileSource(TextureSource):
    """Texture source that loads a single image file from disk.

    Supports both synchronous and asynchronous loading, and caches the
    loaded texture so subsequent requests return the same instance.
    """

    cached = True

    def __init__(self, filename, attribution=None, context=None):
        TextureSource.__init__(self, attribution)
        self.filename = filename
        self.context = context
        self.loaded = False

    def texture_name(self, patch):
        return self.filename

    def texture_filename(self, patch):
        return self.context.find_texture(self.filename)

    async def load(self, tasks_tree, patch, texture_config=None):
        """Load the texture from disk if not already loaded.

        Args:
            tasks_tree: Task tree for async scheduling.
            patch: The patch requesting the texture.
            texture_config: Optional ``TextureConfiguration`` applied after loading.

        Returns:
            Tuple of (Texture, texture_size, texture_lod).
        """
        if not self.loaded:
            if settings.debug_tex_loading:
                logger.debug(f"Loading {self.filename}")
            filename = self.context.find_texture(self.filename)
            if filename is not None:
                if settings.sync_texture_load:
                    texture = workers.syncTextureLoader.load_texture(filename)
                else:
                    texture = await workers.asyncTextureLoader.load_texture(filename, None)
                if texture is not None:
                    if texture_config is not None:
                        texture_config.apply(texture)
                    self.texture = texture
                    self.loaded = True
            else:
                logger.error(f"File {self.filename} not found")
        return (self.texture, 0, 0)

    def clear(self, patch):
        # A non-patched texture can not be cleared per patch
        pass

    def clear_all(self):
        self.texture = None
        self.loaded = False

    def get_texture(self, shape):
        return (self.texture, 0, 0)


class TextureFileSourceFactory(TextureSourceFactory):
    """Factory that creates ``TextureFileSource`` instances for any file extension."""

    def create_source(self, filename, context=None):
        return TextureFileSource(filename, None, context)


# TODO: Should be done in cosmonium class
# Priority is set to a high value (ie low priority) as this is the fallback factory
AutoTextureSource.register_source_factory(TextureFileSourceFactory(), [], 9999)


class DirectTextureSource(TextureSource):
    """Texture source that wraps an already-loaded Panda3D ``Texture`` object.

    Useful for procedurally generated or externally managed textures that
    do not need file-based loading.
    """

    cached = False

    def __init__(self, texture):
        TextureSource.__init__(self)
        self.loaded = True
        self.replace(texture)

    def replace(self, texture):
        """Replace the wrapped texture with a new one."""
        self.texture = texture

    async def load(self, tasks_tree, patch):
        return (self.texture, 0, 0)

    def get_texture(self, shape):
        return (self.texture, 0, 0)


class VirtualTextureSource(TextureSource):
    """Patched LOD texture source with per-patch file loading.

    Manages a sparse map of loaded patches, loading textures on demand
    from a directory tree organised by LOD level. When a patch's own texture is
    unavailable, the nearest loaded ancestor texture is returned as a fallback.
    """

    cached = False

    def __init__(self, root, ext, size, attribution=None, context=None):
        """Initialize the virtual texture source with the given root directory, file extension, and texture size.

        Args:
            root: Root directory containing the textures organised by LOD.
            ext: File extension for the texture files (e.g. 'png').
            size: Texture size in pixels (assumed square).
            attribution: Optional attribution string for the texture source.
            context: Directory context for resolving texture file paths.
        """
        TextureSource.__init__(self, attribution)
        assert context is not None, "Context is required for VirtualTextureSource"
        self.map_patch = {}
        self.root = root
        self.ext = ext
        self.texture_size = size
        self.context = context

    def is_patched(self):
        return True

    def child_texture_name(self, patch) -> str:
        """Return the filename for a child texture corresponding to the given patch.
        Note: Only used for checking the existence of higher-resolution texture,
        not for actual loading (which uses texture_name)."""
        raise NotImplementedError()

    def texture_name(self, patch) -> str:
        """Return the filename for the texture corresponding to the given patch."""
        raise NotImplementedError()

    def alpha_texture_name(self, patch) -> str | None:
        """Return the filename for the alpha texture corresponding to the given patch,
        or None if not applicable."""
        raise NotImplementedError()

    def can_split(self, patch):
        """Check whether a higher-resolution child texture exists on disk for the patch."""
        tex_name = self.child_texture_name(patch)
        exists = os.path.isfile(tex_name)
        return exists

    def find_parent_texture_for(self, patch):
        """Walk up the patch hierarchy to find the nearest loaded ancestor texture."""
        parent_patch = patch.parent
        while parent_patch is not None and parent_patch.str_id() not in self.map_patch:
            parent_patch = parent_patch.parent
        if parent_patch is not None:
            return self.map_patch[parent_patch.str_id()]

    async def load(self, tasks_tree, patch, texture_config=None):
        """Load the texture for a patch, falling back to the nearest ancestor.

        Args:
            tasks_tree: Task tree for async scheduling.
            patch: The terrain patch requesting its texture.
            texture_config: Optional ``TextureConfiguration`` applied after loading.

        Returns:
            Tuple of (Texture, texture_size, texture_lod), or ``None`` if
            no texture could be loaded.
        """
        texture_info = None
        if not patch.str_id() in self.map_patch:
            tex_name = self.texture_name(patch)
            if settings.debug_tex_loading:
                logger.debug(f"Load {tex_name}")
            filename = self.context.find_texture(tex_name)
            alpha_tex_name = self.alpha_texture_name(patch)
            alpha_filename = self.context.find_texture(alpha_tex_name)
            if filename is not None:
                if settings.sync_texture_load:
                    texture = workers.syncTextureLoader.load_texture(filename, alpha_filename)
                else:
                    texture = await workers.asyncTextureLoader.load_texture(filename, alpha_filename)
                if texture is not None:
                    if texture_config is not None:
                        texture_config.apply(texture)
                    texture_info = (texture, self.texture_size, patch.lod)
                    self.map_patch[patch.str_id()] = texture_info
            else:
                if settings.debug_tex_loading:
                    logger.warning(f"File {tex_name} not found")
            if texture_info is None:
                texture_info = self.find_parent_texture_for(patch)
        else:
            texture_info = self.map_patch[patch.str_id()]
        return texture_info

    def clear(self, patch):
        """Clear the loaded texture for a specific patch, if it exists."""
        try:
            del self.map_patch[patch.str_id()]
        except KeyError:
            pass

    def clear_all(self):
        """Clear all loaded textures."""
        self.map_patch = {}

    def get_texture(self, patch, strict=False):
        """Retrieve the loaded texture for a patch.

        Args:
            patch: The terrain patch.
            strict: If True, only return the patch's own texture (no ancestor
                fallback).

        Returns:
            Tuple of (Texture, texture_size, texture_lod).
        """
        if patch.str_id() in self.map_patch:
            return self.map_patch[patch.str_id()]
        elif not strict:
            texture_info = self.find_parent_texture_for(patch)
            if texture_info is not None:
                return texture_info
        return (None, self.texture_size, patch.lod)
