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

from typing import TYPE_CHECKING

from panda3d.core import LVector4

from ..skin import UIElement, combine_classes
from .base import DockWidgetBase
from .decorated_sizer import DecoratedSizer

if TYPE_CHECKING:
    from .dock import Dock


class SpaceDockWidget(DockWidgetBase):
    """An empty widget of a fixed size, used to separate adjacent widgets."""

    def __init__(self, width, height, proportions=None, alignments=None, borders=None, index=None):
        DockWidgetBase.__init__(self, proportions, alignments, borders, index)
        self.width = width
        self.height = height

    def add_to(self, dock: Dock, parent, borders, skin) -> None:
        element = parent.element
        width = self.width(element, skin) if self.width is not None else 0
        height = self.height(element, skin) if self.height is not None else 0
        # A sizer takes a plain tuple as an empty cell of the given size.
        self.widget = (width, height)
        DockWidgetBase.add_to(self, dock, parent, borders, skin)


class LayoutDockWidget(DockWidgetBase):
    """A layout of dock widgets, with an optionally decorated frame."""

    def __init__(
        self,
        direction: str,
        widgets: list[DockWidgetBase],
        proportions=None,
        alignments=None,
        borders=None,
        index=None,
        gaps=(0, 0),
        element_class='layout',
        class_=None,
        id_=None,
    ):
        DockWidgetBase.__init__(self, proportions, alignments, borders, index)
        self.direction = direction
        self.element = UIElement('frame', class_=combine_classes(element_class, class_), id_=id_)
        self.widget = DecoratedSizer(self.element, direction, gaps=gaps)
        self.sizer = self.widget
        self.frame = None
        self.widgets = widgets
        self.widget_borders = LVector4(1, 1, 1, 1)

    def default_alignments(self) -> tuple[str, str]:
        """Default alignment for children without explicit alignments.
        Children are packed from the start of the layout direction and centered across it.
        """
        if self.direction == 'horizontal':
            return ('min', 'center')
        else:
            return ('center', 'min')

    def create(self, dock: Dock, parent, skin) -> None:
        self.element.parent = parent.element
        self.widget.create(dock, parent, skin)
        self.instance = parent.instance
        border_x, border_y = self.widget.border
        corner_radius = self.widget.corner_radius
        if corner_radius:
            border_width = max(border_x, border_y)
            # Margin to not overlap the rounded corners
            margin = corner_radius - (corner_radius - border_width) * 0.70710678118654752
            self.widget_borders = LVector4(margin)
        else:
            self.widget_borders = LVector4(border_x, border_x, border_y, border_y)
        for i, widget in enumerate(self.widgets):
            borders = LVector4(0)
            if self.direction == 'horizontal':
                if len(self.widgets) == 1:
                    borders = self.widget_borders
                elif i == 0:
                    borders = LVector4(self.widget_borders[0], 0, self.widget_borders[2], self.widget_borders[3])
                elif i == len(self.widgets) - 1:
                    borders = LVector4(0, self.widget_borders[1], self.widget_borders[2], self.widget_borders[3])
                else:
                    borders = LVector4(0, 0, self.widget_borders[2], self.widget_borders[3])
            else:
                if len(self.widgets) == 1:
                    borders = self.widget_borders
                elif i == 0:
                    borders = LVector4(self.widget_borders[0], self.widget_borders[1], 0, self.widget_borders[3])
                elif i == len(self.widgets) - 1:
                    borders = LVector4(self.widget_borders[0], self.widget_borders[1], self.widget_borders[2], 0)
                else:
                    borders = LVector4(self.widget_borders[0], self.widget_borders[1], 0, 0)
            widget.add_to(dock, self, borders, skin)

    def add_to(self, dock: Dock, parent, borders, skin) -> None:
        DockWidgetBase.add_to(self, dock, parent, borders, skin)
        self.create(dock, parent, skin)
        self.update_layout()

    def update_layout(self):
        min_size = self.sizer.update_min_size()
        self.sizer.update(min_size)

    def update(self, global_vars):
        has_changed = False
        for widget in self.widgets:
            has_changed = widget.update(global_vars) or has_changed
        if has_changed:
            self.update_layout()
        return has_changed
