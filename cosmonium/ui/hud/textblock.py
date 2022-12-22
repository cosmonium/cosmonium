#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2022 Laurent Deru.
#
#Cosmonium is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Cosmonium is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#


from panda3d.core import LVector3
from direct.gui.OnscreenText import OnscreenText, Plain

from ... import settings

from .hud_object import HUDObject


class TextBlock(HUDObject):
    def __init__(self, anchor, scale, offset, align, down, count, font, size, color=None):
        HUDObject.__init__(self, anchor, scale, offset)
        self.align = align
        self.down = down
        self.count = count
        self.text = []
        self.instance = anchor.attach_new_node("anchor")
        self.instances = []
        self.font = font
        self.size = size
        if color is None:
            color = settings.hud_color
        self.color = color
        self.create()
        self.update_instance()

    def get_em_width(self):
        return self.scale[0] * self.textNode.calc_width('M')

    def get_height(self):
        return self.scale[1] * self.size * self.count

    def set_font(self, font):
        self.font = font

    def update_instance(self):
        x_offset = self.offset[0]
        y_offset = self.offset[1]
        height_scale = self.scale[1] * self.size
        if self.down:
            y_offset = -y_offset
        for i in range(self.count):
            if self.down:
                pos_y = -(i + 1)
            else:
                pos_y = i + 0.1
            pos = LVector3(x_offset, 0, pos_y * height_scale + y_offset)
            #self.instance.setScale(*self.scale)
            self.instances[i].set_pos(pos)

    def create_line(self, i):
        return OnscreenText(text="",
                            style=Plain,
                            fg=self.color,
                            scale=tuple(self.scale * self.size),
                            parent=self.instance,
                            align=self.align,
                            font=self.font,
                            mayChange=True)

    def create(self):
        for i in range(self.count):
            self.instances.append(self.create_line(i))
            self.text.append("")

    def set(self, pos, text):
        if self.text[pos] != text:
            self.instances[pos].setText(text)
            self.text[pos] = text
