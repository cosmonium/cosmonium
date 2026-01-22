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

from __future__ import annotations

from direct.gui.DirectFrame import DirectFrame
from panda3d.core import LVector3

from ..core.ui_element import DockedUIElement
from ..skin import UIElement


class Dock(DockedUIElement):

    def __init__(self, id_, direction, location, layout, owner=None):
        DockedUIElement.__init__(self, id_, location, owner)
        self.direction = direction
        self.layout = layout
        self.anchor = None
        self.element = None
        self.pos = LVector3(0)

    def create(self):
        self.element = UIElement('frame', class_='dock', id_=self.id_)
        self.instance = DirectFrame(parent=self.anchor, **self.skin.get_style(self.element))
        self.layout.create(self, self, self.skin)

    def update_instance(self):
        if self.instance is None:
            return
        self.instance.set_pos(self.pos + LVector3(self.offset[0], 0, self.offset[1]))

    def update_size(self):
        self.layout.update_layout()
        size = self.layout.sizer.get_size()
        if self.direction == "horizontal":
            if self.center:
                self.pos[0] = -size[0] / 2
            elif self.location.endswith("left"):
                self.pos[0] = 0
            elif self.location.endswith("right"):
                self.pos[0] = -size[0] - 1
            if self.location.startswith("top"):
                self.pos[2] = -self.offset[1]
            elif self.location.startswith("bottom"):
                self.pos[2] = size[1] + 1
        else:
            if self.location.endswith("left"):
                self.pos[0] = 0
            elif self.location.endswith("right"):
                self.pos[0] = -size[0] - 1
            if self.center:
                self.pos[2] = size[1] / 2
            elif self.location.startswith("top"):
                self.pos[2] = -self.offset[1]
            elif self.location.startswith("bottom"):
                self.pos[2] = size[1] + 1
        self.update_instance()

    def update(self, global_vars):
        self.layout.update(global_vars)
