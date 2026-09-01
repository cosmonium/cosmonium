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

from __future__ import annotations

from math import cos, radians
from typing import Tuple

from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectFrame import DirectFrame
from directguilayout.gui import Sizer
from panda3d.core import TransparencyAttrib

from ...geometry.geometry import FrameGeom
from ..skin import UIElement, UISkin, resolve_edge_lengths, resolve_gap
from ..textures.circle_generator import CircleTextureGenerator

# Cosine of 45 degrees, the direction in which a rounded corner eats the most into the content area
COS_45 = cos(radians(45))


class DecoratedSizer(Sizer):
    """A sizer drawing a skinned frame (background, border and rounded corners) around its content.

    The frame covers the whole area of the sizer, and the content of the container is inset by the border
    width and by the padding.
    """

    def __init__(self, element: UIElement, direction: str, gap=None, padding=None):
        """
        Args:
            element: The skin element of the container
            direction: Direction in which the content is laid out, horizontal or vertical
            gap: Space between the children, overriding the skin, or None
            padding: Edge lengths of the padding, overriding the skin, or None
        """
        Sizer.__init__(self, direction)
        self.element = element
        self.gap = gap
        self.padding = padding
        # The children of the container are added to this sizer, not to the decorated sizer itself
        self.content = Sizer(direction)
        self.frame = None
        self.background_color = None
        self.border_color = None
        self.border_width = 0
        self.corner_radius = 0
        self.corner_texture = None
        self.frame_size = None

    def get_content_inset(self, skin: UISkin) -> Tuple[float, float, float, float]:
        """
        Compute the space between the edges of the frame and the content area.

        The content is inset by the border of the frame and then by its padding.
        Note: When the frame has rounded corners, the border is thicker in the diagonal
        direction than the configured border width so the content does not overlap the corners.

        Args:
            skin: The skin of the ui

        Returns:
            The four edge lengths in pixels, in DirectGUI order (left, right, bottom, top)
        """
        style = skin.get(self.element)
        if self.corner_radius:
            border = self.corner_radius - (self.corner_radius - self.border_width) * COS_45
        else:
            border = self.border_width
        padding = self.padding if self.padding is not None else style.padding
        return tuple(border + length for length in resolve_edge_lengths(padding, self.element, skin))

    def set_declared_size(self, size):
        """
        Apply the size declared by the skin

        Args:
            size: The (width, height) declared by the skin, in pixels
        """
        # default_size is a property managed by the Sizer base class, which is used as the minimal size
        # in each direction.
        self.default_size = size
        # Tell the content to use all the available space in the secondary direction, so that the
        # children are placed relative to the declared size and not to their own natural size.
        if self.prim_dim == 0:
            # Horizontal direction of growing
            self.content.set_row_proportion(0, 1.0)
        else:
            # Vertical direction of growing
            self.content.set_column_proportion(0, 1.0)

    def resolve_style(self, skin: UISkin) -> None:
        """
        Resolve the skin properties defining the box of this container.

        Args:
            skin: The skin of the ui
        """
        style = skin.get(self.element)
        self.background_color = style.background_color
        self.border_color = style.border_color
        self.border_width = style.get_length('border_width', self.element, skin)
        self.corner_radius = style.get_length('border_radius', self.element, skin)
        gap = self.gap if self.gap is not None else style.gap
        self.content.gaps = resolve_gap(gap, self.element, skin)
        # A container with no declared size is sized by its content.
        self.set_declared_size(style.resolved_size(self.element, skin, default=0))

    def setup_content(self, skin: UISkin) -> None:
        """
        Resolve the box of this container and place its content area inside it.

        Args:
            skin: The skin of the ui
        """
        self.resolve_style(skin)
        # The content fills the whole area left over by the border and the padding of the frame.
        self.add(
            self.content,
            proportions=(1.0, 1.0),
            alignments=("expand", "expand"),
            borders=self.get_content_inset(skin),
        )

    def create(self, dock, parent, skin: UISkin) -> None:
        """
        Create the frame of the container and set up its content area.

        Args:
            dock: The dock this container belongs to
            parent: The layout, or the dock, this container is placed in
            skin: The skin of the ui
        """
        self.setup_content(skin)
        frame_style = skin.get_style(self.element)
        if self.corner_radius:
            # With rounded corners, the whole frame is rendered via geometry and texture.
            # But we still need a frame to catch the mouse events, so we need to set the
            # frame color to transparent to avoid overlapping the rounded corners with a solid color.
            frame_style['frameColor'] = (0, 0, 0, 0)
        self.frame = DirectFrame(
            **frame_style,
            parent=parent.instance,
            state=DGG.NORMAL,
        )

    def update_frame(self):
        if self.frame is None:
            # The container is laid out before its frame is created, there is nothing to draw yet.
            return
        size = self.get_size()
        if self.frame_size == size:
            return
        # The frame covers the whole sizer, border box included, the content being inset by the cell
        # holding it, so the size can be used as-is here.
        self.frame['frameSize'] = (0, size[0], -size[1], 0)
        # Create geometry for the frame
        if self.corner_radius:
            # Generate rounded corner texture if corner_radius is specified
            if self.corner_texture is None:
                # Generate circle texture for the border
                generator = CircleTextureGenerator(
                    radius=self.corner_radius,
                    border_width=self.border_width,
                    border_color=self.border_color,
                    inner_color=self.background_color,
                )
                self.corner_texture = generator.generate_circle()
            # Create geometry with UV mapping and texture support
            geom = FrameGeom(size, (self.corner_radius, self.corner_radius), texture=True, fill=True)
            geom.set_texture(self.corner_texture)
            geom.set_transparency(TransparencyAttrib.M_alpha)
        elif self.border_width and self.border_color is not None:
            # Geometry with rectangular border
            geom = FrameGeom(size, (self.border_width, self.border_width), texture=False)
            geom.set_color(*self.border_color)
        else:
            # No visible border, the frame color of the frame itself is all there is to draw
            geom = None
        self.frame['geom'] = geom
        self.frame_size = size

    def set_pos(self, pos):
        Sizer.set_pos(self, pos)
        if self.frame is not None:
            x, y = pos
            self.frame.set_pos(x, 0, -y)

    def set_size(self, size, force=False):
        Sizer.set_size(self, size, force)
        self.update_frame()
