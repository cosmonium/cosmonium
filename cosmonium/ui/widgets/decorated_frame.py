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

"""Background/border/rounded-corner frame decoration."""

from __future__ import annotations

from math import cos, radians
from typing import Optional, Tuple

from panda3d.core import TransparencyAttrib

from ...geometry.geometry import FrameGeom
from ..skin import UIElement, UISkin
from ..textures.circle_generator import CircleTextureGenerator

# Cosine of 45 degrees, the direction in which a rounded corner eats the most into the content area.
COS_45 = cos(radians(45))


class FrameDecoration:
    """Background color, border and rounded-corner geometry for a DirectFrame."""

    def __init__(self, element: UIElement, skin: UISkin):
        style = skin.get(element)
        self.background_color = style.background_color
        self.border_color = style.border_color
        self.border_width = style.get_length('border_width', element, skin)
        self.corner_radius = style.get_length('border_radius', element, skin)
        self._corner_texture = None

    @property
    def has_border(self) -> bool:
        return bool(self.border_width and self.border_color is not None)

    @property
    def content_inset(self) -> float:
        """Extra space the border and, if rounded, the corner eats into the content area.

        A rounded corner needs more clearance than the plain border width so that content placed
        against the edge of the frame does not overlap it.
        """
        if self.corner_radius:
            return self.corner_radius - (self.corner_radius - self.border_width) * COS_45
        return self.border_width

    def frame_color(self) -> Optional[Tuple[float, float, float, float]]:
        """The color to assign to the DirectFrame's own `frameColor`.

        Transparent when rounded corners are drawn via geometry instead (a square background
        would otherwise show past the rounded corner), plain background color otherwise.
        """
        if self.corner_radius:
            return (0, 0, 0, 0)
        return self.background_color

    def build_geom(self, size: Tuple[float, float]):
        """
        Build the geometry to assign to a DirectFrame `geom` option.

        Args:
            size: The (width, height) of the frame, in pixels.

        Returns:
            The geometry, or None when there is nothing to draw.

        Note:
            Must be be called each time the frame size changes.
        """
        if self.corner_radius:
            if self._corner_texture is None:
                generator = CircleTextureGenerator(
                    radius=self.corner_radius,
                    border_width=self.border_width,
                    border_color=self.border_color,
                    inner_color=self.background_color,
                )
                self._corner_texture = generator.generate_circle()
            geom = FrameGeom(size, (self.corner_radius, self.corner_radius), texture=True, fill=True)
            geom.set_texture(self._corner_texture)
            geom.set_transparency(TransparencyAttrib.M_alpha)
            return geom
        elif self.has_border:
            geom = FrameGeom(size, (self.border_width, self.border_width), texture=False)
            geom.set_color(*self.border_color)
            return geom
        return None
