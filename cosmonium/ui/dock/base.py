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

import builtins
from typing import TYPE_CHECKING

from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectGuiBase import DirectGuiWidget
from directguilayout.gui import Widget as SizerWidget
from panda3d.core import PNMImage, Texture

if TYPE_CHECKING:
    from .dock import Dock


class DockWidgetBase:

    def __init__(self, proportions=None, alignments=None, borders=None, index=None):
        self.widget: SizerWidget | tuple = None
        self.proportions = proportions
        self.alignments = alignments
        self.borders = borders
        self.index = index

    def add_to(self, dock: Dock, parent, borders, skin) -> None:
        # A widget that does not have an alignment use the default one from the layout.
        alignments = self.alignments if self.alignments is not None else parent.default_alignments()
        parent.sizer.add(
            self.widget,
            self.proportions,
            alignments,
            (self.borders + borders) if self.borders else borders,
            self.index,
        )

    def compile(self):
        pass

    def update(self, global_vars):
        return False


class DGuiDockWidget(DockWidgetBase):

    def __init__(self, proportions=None, alignments=None, borders=None, index=None, enabled=None):
        DockWidgetBase.__init__(self, proportions, alignments, borders, index)
        self.enabled_condition = enabled
        self.is_enabled = True

    def create(self, dock: Dock, parent, messenger, skin) -> DirectGuiWidget:
        raise NotImplementedError()

    def add_to(self, dock: Dock, parent, borders, skin) -> None:
        instance = self.create(dock, parent, builtins.base.messenger, skin)
        instance.reparent_to(dock.instance)
        self.widget = SizerWidget(instance)
        DockWidgetBase.add_to(self, dock, parent, borders, skin)

    def update(self, global_vars):
        if self.enabled_condition is None:
            return False
        enabled = bool(self.enabled_condition.execute(global_vars))
        if enabled == self.is_enabled:
            return False
        self.is_enabled = enabled
        self.widget.dgui_obj['state'] = DGG.NORMAL if enabled else DGG.DISABLED
        return False


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
