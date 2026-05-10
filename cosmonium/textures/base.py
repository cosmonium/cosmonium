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

"""Abstract base classes for texture wrappers and texture sources.

:class:`TextureBase` defines the interface shared by all texture wrappers.
:class:`TextureSource` defines the interface shared by all texture loading
strategies.
"""

from panda3d.core import PNMImage, Texture


class TextureBase:
    """Abstract base class for all texture wrappers.

    Defines the interface shared by every texture type: loading,
    applying to scene instances, clearing, and LOD splitting. Subclasses
    override these methods to implement specific texture behaviours.
    """

    default_texture = None

    def __init__(self):
        self.panda = True
        self.input_name = None

    def use(self, count=1):
        pass

    def release(self, count=1):
        pass

    def set_target(self, panda, input_name=None):
        """Configure whether the texture is applied via Panda3D stages or as a shader input."""
        self.panda = panda
        self.input_name = input_name

    def add_as_source(self, shape):
        """Add this texture as a source to the given shape, if applicable (e.g. for patched textures)."""
        pass

    def set_offset(self, offset):
        """Set the UV offset for the texture, if applicable."""
        pass

    async def load(self, tasks_tree, patch):
        """Load the texture data for the given patch if not already loaded.

        Args:
            tasks_tree: Task tree for async scheduling.
            patch: The patch requesting the texture or None if not applicable.
        """
        pass

    def apply(self, shape, instance):
        """Apply the texture to a scene instance, using Panda3D stages."""
        pass

    def apply_shader(self, instance, input_name, texture, texture_lod):
        """Apply the texture to a scene instance, using shader input."""
        instance.set_shader_input(input_name, texture)

    def clear(self, patch):
        """Unload or clear the texture data for a specific patch, if applicable."""
        pass

    def clear_all(self):
        """Unload or clear all texture data managed by this wrapper."""
        pass

    def can_split(self, patch):
        """Return True if this texture can be split into higher-resolution textures for the given patch."""
        return False

    def get_default_nb_components(self):
        """Return the number of color components for the default texture (e.g. 4 for RGBA)."""
        return 4

    def get_default_max_val(self):
        """Return the maximum pixel value for the default texture (e.g. 255 for 8-bit textures)."""
        return 255

    def get_default_color(self):
        """Return the default color for this texture as an RGBA tuple to use if the texture is unavailable."""
        return (1, 1, 1, 1)

    def create_default_image(self):
        """Create a 1×1 PNMImage filled with this texture's default color, used if the texture is unavailable."""
        image = PNMImage(1, 1, self.get_default_nb_components(), self.get_default_max_val())
        image.setXelA(0, 0, self.get_default_color())
        return image

    def create_default_texture(self):
        """Create a fallback 1×1 texture used when the real texture is unavailable.

        Returns:
            Tuple of (Texture, texture_size, texture_lod).
        """
        image = self.create_default_image()
        texture = Texture()
        texture.load(image)
        return (texture, 0, 0)

    def get_default_texture(self):
        """Return the cached default texture, creating it on first access."""
        if self.default_texture is None:
            self.default_texture = self.create_default_texture()
        return self.default_texture


class TextureSource:
    """Abstract base for texture loading strategies.

    A texture source knows how to locate, load, cache, and clear texture
    data. Concrete subclasses implement file-based,
    procedural, or virtual-texturing loading strategies.
    """

    cached = True
    procedural = False

    def __init__(self):
        """Initialize the texture source."""
        self.loaded = False
        self.texture = None
        self.texture_size = 0
        self.attribution = None

    def set_attribution(self, attribution):
        """Set the attribution metadata for this texture source.

        Args:
            attribution: The attribution string.
        """
        self.attribution = attribution

    def add_as_source(self, shape):
        """Add this texture source as a source to the given shape, if applicable (e.g. for patched textures)."""
        pass

    def is_patched(self):
        """Return True if this texture source is a patched (virtual) texture that manages multiple textures."""
        return False

    def set_offset(self, offset):
        """Set the UV offset for the textures, if applicable."""
        pass

    def texture_name(self, patch):
        """Return the filename or identifier for the texture corresponding to the given patch, if applicable."""
        return None

    def texture_filename(self, patch):
        """Return the resolved filename for the texture corresponding to the given patch, if applicable."""
        return None

    async def load(self, tasks_tree, patch, texture_config=None):
        """Load the texture data for the given patch if not already loaded.
        Args:
            tasks_tree: Task tree for async scheduling.
            patch: The patch requesting the texture or None if not applicable.
            texture_config: Optional ``TextureConfiguration`` applied after loading.
        """
        pass

    def clear(self, patch):
        """Unload or clear the texture data for a specific patch, if applicable."""
        pass

    def clear_all(self):
        """Unload or clear all texture data, if applicable."""
        pass

    def can_split(self, patch):
        """Return True if this texture can be split into higher-resolution textures for the given patch."""
        return False

    def get_texture(self, patch):
        """Return the texture for the given patch, or a default texture if not available."""
        return (None, 0, 0)

    def get_recommended_shape(self):
        """Return the recommended shape for this texture, if applicable."""
        return None
