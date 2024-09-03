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

from directguilayout.gui import Widget as SizerWidget
from direct.gui.DirectGuiBase import DirectGuiWidget
from panda3d.core import PNMImage, Texture


class DockWidgetBase:

    def __init__(self, proportions=None, alignments=None, borders=None, index=None):
        self.widget: SizerWidget | tuple = None
        self.proportions = proportions
        self.alignments = alignments
        self.borders = borders
        self.index = index
        self.update_needed = False

    def add_to(self, dock: Dock, parent, borders, skin) -> None:
        parent.sizer.add(
            self.widget,
            self.proportions,
            self.alignments,
            (self.borders + borders) if self.borders else borders,
            self.index)

    def update(self):
        return False


class DGuiDockWidget(DockWidgetBase):

    def create(self, dock: Dock, parent, messenger, skin) -> DirectGuiWidget:
        raise NotImplementedError()

    def add_to(self, dock: Dock, parent, borders, skin) -> None:
        instance = self.create(dock, parent, base.messenger, skin)
        instance.reparent_to(dock.instance)
        self.widget = SizerWidget(instance)
        DockWidgetBase.add_to(self, dock, parent, borders, skin)


class FrameColorTexture:

    def __init__(self, background_color, border_color):
        self.size = 3
        self.image = PNMImage(self.size, self.size, num_channels=4)
        for i in range(self.size):
            for j in range(self.size):
                self.image.set_xel_a(j, i, *border_color)
        self.image.set_xel_a(1, 1, *background_color)
        self.texture = Texture()
        self.texture.load(self.image)
