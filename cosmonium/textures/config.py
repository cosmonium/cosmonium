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

"""Texture coordinate modes and configuration.

Defines :class:`TexCoord`, an enumeration of texture-coordinate mapping
modes, and :class:`TextureConfiguration`, which encapsulates all Panda3D
texture sampling parameters.
"""

from panda3d.core import LColor, Texture


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
