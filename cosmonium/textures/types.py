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

"""Concrete texture wrapper types.

Provides all renderable and data-channel texture wrappers built on top of
:class:`~cosmonium.textures.base.TextureBase`, ranging from simple
file-backed surfaces to normal maps, specular maps, bump maps, texture
arrays, and height maps.
"""

import logging

from panda3d.core import LColor, Texture, TextureStage

from .. import settings, workers
from ..utils import TransparencyBlend
from .base import TextureBase
from .config import TextureConfiguration
from .sources import AutoTextureSource, TextureSource

logger = logging.getLogger("textures")


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
