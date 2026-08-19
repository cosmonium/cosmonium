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

from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectFrame import DirectFrame
from directguilayout.gui import Sizer
from panda3d.core import TransparencyAttrib

from ...geometry.geometry import FrameGeom
from ..textures.circle_generator import CircleTextureGenerator


class DecoratedSizer(Sizer):
    """A sizer drawing a skinned frame (background, border and rounded corners) behind its content."""

    def __init__(self, element, *args, **kwargs):
        Sizer.__init__(self, *args, **kwargs)
        self.frame = None
        self.border = (0, 0)
        self.element = element
        self.border_color = None
        self.corner_radius = 0
        self.corner_texture = None
        self.frame_size = None

    def set_declared_size(self, size):
        """Apply the size declared by the skin."""
        # default_size is a property managed by the Sizer base class,
        # which is used as the minimal size in each direction.
        self.default_size = size
        # Tell the sizer to use all the available space in the primary direction.
        if self.prim_dim == 0:
            # Horizontal direction of growing
            self.set_row_proportion(0, 1.0)
        else:
            # Vertical direction of growing
            self.set_column_proportion(0, 1.0)

    def create(self, dock, parent, skin):
        skin_entry = skin.get(self.element)
        self.background_color = skin_entry.background_color
        self.border_color = skin_entry.border_color
        if skin_entry.border_width is not None:
            border_val = skin_entry.border_width(self.element, skin)
            self.border = (border_val, border_val)
        if skin_entry.border_radius is not None:
            self.corner_radius = skin_entry.border_radius(self.element, skin)
        self.set_declared_size(skin_entry.resolved_size(self.element, skin, default=0))
        style = skin.get_style(self.element)
        if self.corner_radius:
            # With rounded corners, the whole frame is rendered via geometry and texture.
            # But we still need a frame to catch the mouse events, so we need to set the
            # frame color to transparent to avoid overlapping the rounded corners with a solid color.
            style['frameColor'] = (0, 0, 0, 0)
        self.frame = DirectFrame(
            **style,
            parent=parent.instance,
            state=DGG.NORMAL,
        )

    def update_frame(self):
        if self.frame_size == self.get_size():
            return
        size = self.get_size()
        # The border/corner are taken into account by LayoutDockWidget so no need to add it here.
        frame_size = (0, size[0], -size[1], 0)
        self.frame['frameSize'] = frame_size
        # Create geometry for the frame
        if self.corner_radius:
            # Generate rounded corner texture if corner_radius is specified
            if self.corner_texture is None:
                # Generate circle texture for the border
                generator = CircleTextureGenerator(
                    radius=self.corner_radius,
                    border_width=max(self.border[0], self.border[1]),
                    border_color=self.border_color,
                    inner_color=self.background_color,
                )
                self.corner_texture = generator.generate_circle()
            # Create geometry with UV mapping and texture support
            geom = FrameGeom(size, (self.corner_radius, self.corner_radius), texture=True, fill=True)
            geom.set_texture(self.corner_texture)
            geom.set_transparency(TransparencyAttrib.M_alpha)
            self.frame['geom'] = geom
        else:
            # Geometry with rectangular border
            geom = FrameGeom(size, self.border, texture=False)
            geom.set_color(*self.border_color)
        self.frame['geom'] = geom
        self.frame_size = size

    def set_pos(self, pos):
        Sizer.set_pos(self, pos)
        x, y = pos
        self.frame.set_pos(x, 0, -y)

    def update(self, size=None):
        Sizer.update(self, size=size)
        self.update_frame()
