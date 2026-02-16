#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2025 Laurent Deru.
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

"""Utility class for creating and managing shadow map buffers.

This module provides the ShadowMapBufferCreator class which encapsulates all logic
related to creating and configuring shadow map buffers and depth textures.
"""

from __future__ import annotations

import builtins
from typing import Optional, Tuple
from panda3d.core import WindowProperties, FrameBufferProperties, GraphicsPipe, GraphicsOutput
from panda3d.core import Texture, LColor


class ShadowMapBufferCreator:
    """Handles creation and management of shadow map buffers.

    This class encapsulates the logic for creating render buffers
    that produce depth textures for shadow mapping.

    :ivar base: Reference to the Panda3D base application
    :ivar win: Reference to the main window
    :ivar graphics_engine: Reference to the graphics engine
    """

    def __init__(self) -> None:
        """Initialize the shadow mapper with Panda3D base reference."""
        self.base = builtins.base

    def create_render_buffer(
        self,
        size_x: int,
        size_y: int,
        depth_bits: int,
        depth_tex: Texture,
        color_tex: Texture | None = None,
    ) -> Optional[GraphicsOutput]:
        """Create a render buffer producing a depth texture.

        :param size_x: Width of the buffer in pixels
        :param size_y: Height of the buffer in pixels
        :param depth_bits: Number of depth bits (e.g., 16, 24, 32)
        :param depth_tex: Texture object to receive depth data
        :param color_tex: Optional texture object to receive color data
        :return: The created graphics buffer or None on failure
        """
        # Configure window properties
        window_props = WindowProperties.size(size_x, size_y)
        buffer_props = FrameBufferProperties()

        if color_tex:
            # Set color buffer properties (8-bit RGBA for debugging)
            buffer_props.set_rgba_bits(8, 8, 8, 8)
        else:
            buffer_props.set_rgba_bits(0, 0, 0, 0)
        # Configure buffer properties
        buffer_props.set_accum_bits(0)
        buffer_props.set_stencil_bits(0)
        buffer_props.set_back_buffers(0)
        buffer_props.set_coverage_samples(0)
        buffer_props.set_depth_bits(depth_bits)

        if depth_bits == 32:
            buffer_props.set_float_depth(True)

        buffer_props.set_force_hardware(True)
        buffer_props.set_multisamples(0)
        buffer_props.set_srgb_color(False)
        buffer_props.set_stereo(False)

        # Create the buffer
        self.win = self.base.win
        self.graphics_engine = self.base.graphics_engine
        buffer = self.graphics_engine.make_output(
            self.win.get_pipe(),
            "shadow_buffer",
            1,
            buffer_props,
            window_props,
            GraphicsPipe.BF_refuse_window,
            self.win.gsg,
            self.win,
        )

        if buffer is None:
            print("Failed to create shadow buffer")
            return None

        # Attach depth texture
        buffer.add_render_texture(depth_tex, GraphicsOutput.RTM_bind_or_copy, GraphicsOutput.RTP_depth)

        # Add color texture for debugging
        if color_tex:
            buffer.add_render_texture(color_tex, GraphicsOutput.RTM_bind_or_copy, GraphicsOutput.RTP_color)
            buffer.setClearColor((1, 1, 1, 1))
            buffer.setClearColorActive(True)

        buffer.set_sort(-1000)
        buffer.get_display_region(0).disable_clears()
        buffer.get_overlay_display_region().disable_clears()
        buffer.get_overlay_display_region().set_active(False)

        return buffer

    def create_simple_shadow_buffer(
        self, size: int, name: str = "shadows-buffer", color_tex: bool = False
    ) -> Tuple[Optional[GraphicsOutput], Optional[Texture]]:
        """Create a simple shadow buffer with depth texture.

        :param size: Size of the square shadow map in pixels
        :param name: Name for the buffer (default: "shadows-buffer")
        :return: Tuple of (buffer, depthmap) or (None, None) on failure
        """
        winprops = WindowProperties.size(size, size)
        props = FrameBufferProperties()
        if color_tex:
            props.set_rgb_color(1)
        else:
            props.set_rgb_color(0)
            props.set_alpha_bits(0)
        props.set_depth_bits(1)

        win = self.base.win
        buffer = self.base.graphics_engine.make_output(
            win.get_pipe(), name, -2, props, winprops, GraphicsPipe.BF_refuse_window, win.get_gsg(), win
        )

        if not buffer:
            print("Video driver cannot create an offscreen buffer.")
            return None, None

        depthmap = Texture()
        buffer.add_render_texture(depthmap, GraphicsOutput.RTM_bind_or_copy, GraphicsOutput.RTP_depth_stencil)
        self.configure_shadow_texture(depthmap)

        if color_tex:
            colortex = Texture()
            buffer.add_render_texture(colortex, GraphicsOutput.RTM_bind_or_copy, GraphicsOutput.RTP_color)
            buffer.setClearColor((1, 1, 1, 1))
            buffer.setClearColorActive(True)

        return buffer, depthmap

    def configure_shadow_texture(self, texture: Texture) -> None:
        """Configure texture for shadow mapping use.

        Sets up texture filtering and wrapping modes appropriate for
        shadow map sampling.

        :param texture: The texture to configure
        """
        texture.set_minfilter(Texture.FT_shadow)
        texture.set_magfilter(Texture.FT_shadow)
        texture.set_border_color(LColor(1, 1, 1, 1))
        texture.set_wrap_u(Texture.WM_border_color)
        texture.set_wrap_v(Texture.WM_border_color)
