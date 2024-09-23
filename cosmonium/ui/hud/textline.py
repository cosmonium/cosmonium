#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
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


from panda3d.core import LVector2, LVector3
from direct.gui.OnscreenText import OnscreenText, Plain

from ..skin import UIElement
from .hud_object import HUDObject


class TextLine(HUDObject):
    def __init__(self, id_, align, pos, owner=None):
        HUDObject.__init__(self, id_, owner)
        self.align = align
        self.text = ""
        self.pos = LVector2(pos[0], -pos[1])
        self.scale = None

    def get_height(self):
        return self.scale[1]

    def update_instance(self):
        if self.instance is None:
            return
        x_offset = self.offset[0]
        y_offset = self.offset[1]
        pos = LVector3(self.pos[0] * self.scale[0] + x_offset, 0, self.pos[1] * self.scale[1] + y_offset)
        self.instance.set_pos(pos)

    def set_pos(self, pos):
        self.pos = (pos[0], -pos[1])
        self.update_instance()

    def set_parent(self, parent):
        if parent != self.anchor:
            self.anchor = parent
            self.instance.reparent_to(self.anchor)

    def create(self):
        text_line_element = UIElement('onscreen-text', parent=self.owner.element, id_=self.id_)
        style = self.skin.get_style(text_line_element)
        self.scale = style['scale']
        self.instance = OnscreenText(
            text="", style=Plain, parent=self.anchor, align=self.align, mayChange=True, **style
        )
        self.update_instance()

    def set_text(self, text):
        self.instance.setText(text)
        self.text = text

    def set_all(self, text, pos, anchor):
        self.set_text(text)
        self.set_parent(anchor)
        self.set_pos(pos)
