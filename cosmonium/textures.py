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

This module separates texture *sources* (how texture data is
obtained) from texture *wrappers* (how textures are configured and applied
to scene geometry).
"""

import logging
import os

from panda3d.core import LColor, PNMImage, Texture, TextureStage

from . import settings, workers
from .dircontext import defaultDirContext
from .utils import TransparencyBlend

logger = logging.getLogger("textures")


class TexCoord:
    """Enumeration of texture coordinate mapping modes.

    Defines how 3D surface positions are mapped to 2D texture coordinates
    for different geometry types.
    """

    Flat = 0
    Cylindrical = 1
    NormalizedCube = 2
    SqrtCube = 3


class TextureConfiguration:
    """Configuration for Panda3D texture wrapping, filtering, and format.

    Encapsulates all texture sampling parameters (wrap modes, anisotropic
    filtering, min/mag filters, border color, pixel format) and provides
    helpers to create new textures or apply settings to existing ones.
    """

    def __init__(
        self,
        *,
        wrap_u=Texture.WM_repeat,
        wrap_v=Texture.WM_repeat,
        wrap_w=Texture.WM_repeat,
        anisotropic_degree=0,
        minfilter=Texture.FT_default,
        magfilter=Texture.FT_default,
        border_color=LColor(0, 0, 0, 1),
        format=None,
        convert_to_srgb=False,
    ):
        """Initialize the texture configuration with the given parameters.

        Args:
            wrap_u: Texture.WM_* mode for U coordinate wrapping.
            wrap_v: Texture.WM_* mode for V coordinate wrapping.
            wrap_w: Texture.WM_* mode for W coordinate wrapping (3D textures).
            anisotropic_degree: Anisotropic filtering degree (0 to disable).
            minfilter: Texture.FT_* mode for minification filtering.
            magfilter: Texture.FT_* mode for magnification filtering.
            border_color: LColor used when wrap mode is WM_border_color.
            format: Optional Texture.F_* pixel format to set on created textures.
            convert_to_srgb: If True, convert loaded textures to sRGB format if applicable.
        """
        self.wrap_u = wrap_u
        self.wrap_v = wrap_v
        self.wrap_w = wrap_w
        self.anisotropic_degree = anisotropic_degree
        self.minfilter = minfilter
        self.magfilter = magfilter
        self.border_color = border_color
        self.format = format
        self.convert_to_srgb = convert_to_srgb

    def create_2d(self, name, width, height):
        """Create a new 2D Panda3D texture with this configuration applied.

        Args:
            name: Display name for the texture.
            width: Width in pixels.
            height: Height in pixels.

        Returns:
            A configured ``Texture`` instance.
        """
        if self.format in (Texture.F_rgba32, Texture.F_rgb32, Texture.F_rg32, Texture.F_r32):
            c_type = Texture.T_float
        elif self.format in (Texture.F_rgba16, Texture.F_rgb16, Texture.F_rg16, Texture.F_r16):
            c_type = Texture.T_half_float
        else:
            c_type = Texture.T_byte
        texture = Texture(name)
        texture.setup_2d_texture(width, height, c_type, self.format)
        self.apply(texture)
        return texture

    def apply(self, texture):
        """Apply this configuration's sampling and format settings to a texture."""
        if self.format is not None:
            texture.set_format(self.format)
        texture.set_wrap_u(self.wrap_u)
        texture.set_wrap_v(self.wrap_v)
        texture.set_wrap_w(self.wrap_w)
        texture.set_anisotropic_degree(self.anisotropic_degree)
        texture.set_minfilter(self.minfilter)
        texture.set_magfilter(self.magfilter)
        texture.set_border_color(self.border_color)
        if self.convert_to_srgb:
            texture_format = texture.get_format()
            if texture_format == Texture.F_luminance:
                texture.set_format(Texture.F_sluminance)
            elif texture_format == Texture.F_luminance_alpha:
                texture.set_format(Texture.F_sluminance_alpha)
            elif texture_format == Texture.F_rgb:
                texture.set_format(Texture.F_srgb)
            elif texture_format == Texture.F_rgba:
                texture.set_format(Texture.F_srgb_alpha)


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

    def __init__(self, attribution=None):
        """Initialize the texture source with optional attribution metadata."""
        self.loaded = False
        self.texture = None
        self.texture_size = 0
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

    def __init__(self, filename, attribution=None, context=defaultDirContext):
        """Initialize the auto texture source with the given filename and context.
        Args:
            filename: The file path or identifier for the texture to load.
            attribution: Optional attribution string for the texture source.
            context: Directory context for resolving texture file paths.
        """
        TextureSource.__init__(self, attribution)
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
        """Returbn the resolved filename for the texture corresponding to the given patch, if applicable."""
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

    def create_source(self, filename, context=defaultDirContext):
        return None


class TextureFileSource(TextureSource):
    """Texture source that loads a single image file from disk.

    Supports both synchronous and asynchronous loading, and caches the
    loaded texture so subsequent requests return the same instance.
    """

    cached = True

    def __init__(self, filename, attribution=None, context=defaultDirContext):
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

    def create_source(self, filename, context=defaultDirContext):
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


class WrapperTexture(TextureBase):
    """Thin wrapper around an existing texture instance.

    Exposes the standard ``TextureBase`` interface for a texture that is
    already fully constructed elsewhere.
    """

    def __init__(self, texture):
        self.texture = texture
        self.source = TextureSource()


class SimpleTexture(TextureBase):
    """Basic texture wrapper with source-driven loading and LOD support.

    Manages a ``TextureSource``, creates appropriate texture configurations
    based on patch LOD and border settings, and applies the loaded texture
    to scene instances via Panda3D texture stages or shader inputs.
    """

    def __init__(self, source, srgb=False, offset=0):
        TextureBase.__init__(self)
        if source is not None and not isinstance(source, TextureSource):
            source = AutoTextureSource(source, attribution=None)
        self.srgb = srgb
        self.source = source
        self.offset = offset
        self.tex_matrix = True

    def add_as_source(self, shape):
        self.source.add_as_source(shape)

    def set_offset(self, offset):
        self.offset = offset

    def set_tex_matrix(self, tex_matrix):
        self.tex_matrix = tex_matrix

    def init_texture_stage(self, texture_stage, texture):
        pass

    def configure_instance(self, instance):
        pass

    def create_texture_config(self, shape):
        """Build a ``TextureConfiguration`` tailored to the current shape and LOD."""
        texture_config = TextureConfiguration()
        texture_config.convert_to_srgb = self.srgb
        if self.source.is_patched():
            texture_config.wrap_u = Texture.WM_clamp
            texture_config.wrap_v = Texture.WM_clamp
        if not self.source.is_patched():
            texture_config.minfilter = Texture.FT_linear_mipmap_linear
            texture_config.magfilter = Texture.FT_linear_mipmap_linear
        else:
            if shape.lod == 0:
                texture_config.minfilter = Texture.FT_linear_mipmap_linear
                texture_config.magfilter = Texture.FT_linear
            else:
                texture_config.minfilter = Texture.FT_linear
                texture_config.magfilter = Texture.FT_linear
        if shape.vanish_borders:
            texture_config.wrap_u = Texture.WM_border_color
            texture_config.border_color = LColor(0, 0, 0, 0)
        return texture_config

    async def load(self, tasks_tree, patch):
        """Load the texture data for the given patch if not cached."""
        if not self.source.loaded or not self.source.cached:
            if self.source.is_patched():
                self.source.set_offset(self.offset)
            texture_config = self.create_texture_config(patch)
            (texture, texture_size, texture_lod) = await self.source.load(
                tasks_tree, patch, texture_config=texture_config
            )

    def apply(self, shape, instance):
        """Apply the loaded texture to a scene instance, falling back to a default if needed."""
        (texture, texture_size, texture_lod) = self.source.get_texture(shape)
        if texture is None:
            if settings.debug_tex_loading:
                logger.debug(f"Use default texture for {shape.str_id()}")
            (texture, texture_size, texture_lod) = self.get_default_texture()
        # TODO: not really apply but we need a place to detected the alpha channel
        self.has_alpha_channel = texture.get_format() in (
            Texture.F_rgba,
            Texture.F_srgb_alpha,
            Texture.F_luminance_alpha,
            Texture.F_sluminance_alpha,
        )
        if self.panda:
            self.apply_panda(shape, instance, texture, texture_lod)
        else:
            self.apply_shader(instance, self.input_name, texture, texture_lod)
        self.configure_instance(shape.instance)

    def apply_panda(self, shape, instance, texture, texture_lod):
        """Apply the texture using Panda3D's texture-stage pipeline."""
        texture_stage = TextureStage(shape.str_id() + self.__class__.__name__)
        self.init_texture_stage(texture_stage, texture)
        if self.tex_matrix:
            shape.set_texture_to_lod(self, texture_stage, texture_lod, self.source.is_patched())
        instance.set_texture(texture_stage, texture, 1)

    def clear(self, patch):
        self.source.clear(patch)

    def clear_all(self):
        self.source.clear_all()

    def can_split(self, patch):
        return self.source.can_split(patch)


class DataTexture(TextureBase):
    """Non-visible data texture applied only as a shader input.

    Used for data channels such as heightmaps or lookup tables that are
    consumed by shaders rather than rendered directly as surface color.
    """

    def __init__(self, source):
        TextureBase.__init__(self)
        if source is not None and not isinstance(source, TextureSource):
            source = AutoTextureSource(source, attribution=None)
        self.source = source

    async def load(self, tasks_tree, patch, texture_config):
        """Load the data texture using the provided configuration."""
        if not self.source.loaded or not self.source.cached:
            await self.source.load(tasks_tree, patch, texture_config=texture_config)

    def apply(self, shape, instance, input_name):
        """Bind the texture as a shader input on the given instance."""
        (texture, texture_size, texture_lod) = self.source.get_texture(shape)
        if texture is None:
            (texture, texture_size, texture_lod) = self.get_default_texture()
        if texture is not None:
            instance.set_shader_input(input_name, texture)

    def clear(self, patch, instance):
        self.source.clear(patch)

    def clear_all(self):
        self.source.clear_all()

    def can_split(self, patch):
        return self.source.can_split(patch)


class VisibleTexture(SimpleTexture):
    """Renderable texture with optional color tinting.

    Extends ``SimpleTexture`` with tint color support and transparency.
    """

    def __init__(self, source, tint=None, srgb=None):
        if srgb is None:
            srgb = settings.use_srgb
        SimpleTexture.__init__(self, source, srgb=srgb)
        self.tint_color = tint
        self.transparent = False
        self.has_alpha_channel = False
        self.has_specular_mask = False

    def init_texture_stage(self, texture_stage, texture):
        """Configure the texture stage to apply tint color modulation."""
        if self.tint_color is not None:
            if settings.disable_tint:
                return
            texture_stage.setColor(self.tint_color)
            texture_stage.setCombineRgb(
                TextureStage.CMModulate,
                TextureStage.CSTexture,
                TextureStage.COSrcColor,
                TextureStage.CSConstant,
                TextureStage.COSrcColor,
            )


class SurfaceTexture(VisibleTexture):
    """Surface albedo texture."""

    category = 'albedo'

    def __init__(self, source, tint=None, srgb=None):
        VisibleTexture.__init__(self, source, tint, srgb=srgb)
        self.transparent = False

    def init_texture_stage(self, texture_stage, texture):
        VisibleTexture.init_texture_stage(self, texture_stage, texture)
        if self.has_specular_mask:
            texture_stage.setMode(TextureStage.MModulateGloss)

    def get_default_color(self):
        return (1, 1, 1, 1)


class EmissionTexture(SurfaceTexture):
    """Emission (night-side / self-illumination) texture.

    Defaults to black (no emission) when no texture data is available.
    """

    def get_default_color(self):
        return (0, 0, 0, 1)


class TransparentTexture(VisibleTexture):
    """Texture with explicit alpha transparency and configurable blend mode.

    Always marked transparent; applies the chosen ``TransparencyBlend``
    mode to the scene instance during rendering.
    """

    category = 'albedo'

    def __init__(self, source, tint=None, level=0.0, blend=TransparencyBlend.TB_Alpha, srgb=None):
        VisibleTexture.__init__(self, source, tint, srgb)
        self.level = level
        self.transparent = True
        self.blend = blend

    def configure_instance(self, instance):
        TransparencyBlend.apply(self.blend, instance)

    def get_default_color(self):
        return (1, 1, 1, 0)


class NormalMapTexture(SimpleTexture):
    """Normal map texture for per-pixel surface lighting.

    Defaults to a flat normal (0.5, 0.5, 1.0) when no texture is loaded.
    """

    category = 'normal'

    def init_texture_stage(self, texture_stage, texture):
        texture_stage.setMode(TextureStage.MNormal)

    def get_default_color(self):
        return (0.5, 0.5, 1, 1)


class SpecularMapTexture(SimpleTexture):
    """Specular/gloss map texture controlling surface shininess."""

    category = 'specular'

    def init_texture_stage(self, texture_stage, texture):
        texture_stage.setMode(TextureStage.MGloss)

    def get_default_color(self):
        return (1, 1, 1, 1)


class OcclusionMapTexture(SimpleTexture):
    """Ambient occlusion map texture for indirect lighting attenuation."""

    category = 'occlusion'

    def get_default_color(self):
        return (1, 1, 1, 1)


class BumpMapTexture(SimpleTexture):
    """Height/bump map texture for surface displacement effects."""

    category = 'bump'

    def init_texture_stage(self, texture_stage, texture):
        texture_stage.setMode(TextureStage.MHeight)

    def get_default_color(self):
        return (0, 0, 0, 0)


class TextureArray(TextureBase):
    """Array of textures combined into a single Panda3D texture array."""

    def __init__(self, textures=None, srgb=False):
        TextureBase.__init__(self)
        if textures is None:
            textures = []
        self.textures = textures
        if not settings.use_srgb:
            srgb = False
        self.srgb = srgb
        for i, texture in enumerate(textures):
            # TODO: should be done properly with an accessor or a map in this class
            texture.array_id = i
        self.texture = None
        self.texture_size = 0
        self.texture_lod = 0

    def add_texture(self, texture):
        """Append a texture to the array and assign it a layer index."""
        self.textures.append(texture)
        # TODO: should be done properly with an accessor or a map in this class
        texture.array_id = len(self.textures) - 1

    def set_target(self, panda, input_name=None):
        self.panda = panda
        self.input_name = input_name

    def create_texture_config(self, shape):
        """Build a texture configuration for the combined texture array."""
        texture_config = TextureConfiguration(
            minfilter=Texture.FT_linear_mipmap_linear,
            magfilter=Texture.FT_linear_mipmap_linear,
            convert_to_srgb=self.srgb,
        )
        return texture_config

    async def load(self, tasks_tree, patch):
        """Load all constituent textures and combine them into a texture array."""
        if self.texture is None:
            texture_config = self.create_texture_config(patch)
            if settings.sync_texture_load:
                texture = workers.syncTextureLoader.load_texture_array(self.textures)
            else:
                texture = await workers.asyncTextureLoader.load_texture_array(self.textures)
            if texture is not None:
                self.texture = texture
                texture_config.apply(texture)

    def apply(self, shape, instance):
        self.apply_shader(instance, self.input_name, self.texture, None)

    def clear(self, patch):
        # A non-patched texture can not be cleared per patch
        pass

    def clear_all(self):
        self.texture = None

    def can_split(self, patch):
        return False


class HeightMapTexture(DataTexture):
    """Height map data texture providing elevation data to shaders.

    Single-channel texture that defaults to zero (minimum elevation) when
    no height data is available.
    """

    category = 'heightmap'

    def get_default_nb_components(self):
        return 1

    def get_default_color(self):
        return (0, 0, 0, 0)


class VirtualTextureSource(TextureSource):
    """Patched LOD texture source with per-patch file loading.

    Manages a sparse map of loaded patches, loading textures on demand
    from a directory tree organised by LOD level. When a patch's own texture is
    unavailable, the nearest loaded ancestor texture is returned as a fallback.
    """

    cached = False

    def __init__(self, root, ext, size, attribution=None, context=defaultDirContext):
        """Initialize the virtual texture source with the given root directory, file extension, and texture size.

        Args:
            root: Root directory containing the textures organised by LOD.
            ext: File extension for the texture files (e.g. 'png').
            size: Texture size in pixels (assumed square).
            attribution: Optional attribution string for the texture source.
            context: Directory context for resolving texture file paths.
        """
        TextureSource.__init__(self, attribution)
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
