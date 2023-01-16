#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2023 Laurent Deru.
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

from .base import DockWidgetBase
from .decorated_size import DecoratedSizer
from panda3d.core import LVector4


class SpaceDockWidget(DockWidgetBase):

    def __init__(self, size: tuple, proportions=None, alignments=None, borders=None, index=None):
        DockWidgetBase.__init__(self, proportions, alignments, borders, index)
        self.widget = size


class LayoutDockWidget(DockWidgetBase):

    def __init__(
            self,
            size: int,
            direction: str,
            widgets: list[DockWidgetBase],
            decoration_size: tuple[int],
            image=None,
            geom=None,
            background_color=None,
            border_color=None,
            proportions=None,
            alignments=None,
            borders=None,
            index=None,
            gaps=(0, 0)):
        DockWidgetBase.__init__(self, proportions, alignments, borders, index)
        self.size = size
        self.direction = direction
        self.decoration_size = decoration_size
        self.widget = DecoratedSizer(self.decoration_size, image, geom, border_color, direction, gaps=gaps)
        self.sizer = self.widget
        self.frame = None
        self.widgets = widgets
        self.update_needed = False

    def create(self, dock: Dock, parent, skin) -> None:
        self.widget.create(dock.instance, skin)
        for i, widget in enumerate(self.widgets):
            borders = LVector4(0)
            if self.direction == 'horizontal':
                if len(self.widgets) == 1:
                    borders = LVector4(
                        self.decoration_size[0], self.decoration_size[0],
                        self.decoration_size[1], self.decoration_size[1])
                elif i == 0:
                    borders = LVector4(self.decoration_size[0], 0, self.decoration_size[1], self.decoration_size[1])
                elif i == len(self.widgets) - 1:
                    borders = LVector4(0, self.decoration_size[0], self.decoration_size[1], self.decoration_size[1])
                else:
                    borders = LVector4(0, 0, self.decoration_size[1], self.decoration_size[1])
            else:
                if len(self.widgets) == 1:
                    borders = LVector4(
                        self.decoration_size[0], self.decoration_size[0],
                        self.decoration_size[1], self.decoration_size[1])
                elif i == 0:
                    borders = LVector4(self.decoration_size[0], self.decoration_size[0], 0, self.decoration_size[1])
                elif i == len(self.widgets) - 1:
                    borders = LVector4(self.decoration_size[0], self.decoration_size[0], self.decoration_size[1], 0)
                else:
                    borders = LVector4(self.decoration_size[0], self.decoration_size[0], 0, 0)
            widget.add_to(dock, self, borders, skin)
            if widget.update_needed:
                self.update_needed = True

    def add_to(self, dock: Dock, parent, borders, skin) -> None:
        DockWidgetBase.add_to(self, dock, parent, borders, skin)
        self.create(dock, parent, skin)
        self.update_layout()

    def update_layout(self):
        min_size = self.sizer.update_min_size()
        (width, height) = min_size
        self.sizer.update((width, height))

    def update(self):
        for widget in self.widgets:
            if widget.update_needed:
                widget.update()
