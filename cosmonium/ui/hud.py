#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2019 Laurent Deru.
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

from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import TextNode, LColor, LVector3

from direct.gui.OnscreenText import OnscreenText, Plain
from direct.gui.DirectGui import DirectEntry
from direct.interval.IntervalGlobal import Sequence, Wait

from .. import settings

class HUDObject(object):
    def __init__(self, anchor, scale):
        self.anchor = anchor
        self.scale = scale
        self.shown = True
        self.instance = None

    def hide(self):
        self.instance.hide()
        self.shown = False

    def show(self):
        self.instance.show()
        self.shown = True

    def set_scale(self, scale):
        self.scale = scale
        self.update_instance()

class TextLine(HUDObject):
    def __init__(self, anchor, scale, y_offset, align, down, pos, font, size, color=None):
        HUDObject.__init__(self, anchor, scale)
        if down:
            y_offset = -y_offset
        self.y_offset = y_offset
        self.align = align
        self.down = down
        self.text = ""
        self.instance = None
        self.font = font
        self.size = size
        if self.down:
            self.pos = -(pos + 1)
        else:
            self.pos = pos + 0.1
        if color is None:
            color = LColor(1, 1, 1, 1)
        self.color = color
        self.instance = self.create()

    def get_height(self):
        return self.scale[1] * self.size

    def set_font(self, font):
        self.font = font

    def update_instance(self):
        if self.instance is not None:
            #self.instance.setScale(*self.scale)
            self.instance.setPos(0, self.pos * self.get_height() + self.y_offset)

    def set_y_offset(self, y_offset):
        if self.down:
            y_offset = -y_offset
        self.y_offset = y_offset
        self.update_instance()

    def create(self):
        return OnscreenText(text="",
                            style=Plain,
                            fg=self.color,
                            scale=tuple(self.scale * self.size),
                            parent=self.anchor,
                            pos=(0, self.pos * self.get_height() + self.y_offset),
                            align=self.align,
                            font=self.font,
                            mayChange=True)

    def set(self, text):
        self.instance.setText(text)
        self.text = text

class FadeTextLine(TextLine):
    def __init__(self, *args, **kwargs):
        TextLine.__init__(self, *args, **kwargs)
        self.fade_sequence = None

    def set(self, text, duration=3.0, fade=1.0):
        TextLine.set(self, text)
        self.instance.setColorScale(LColor(1, 1, 1, 1))
        if self.fade_sequence is not None:
            self.fade_sequence.pause()
        self.fade_sequence = Sequence(Wait(duration),
                                      self.instance.colorScaleInterval(fade, LColor(1, 1, 1, 0)))
        self.fade_sequence.start()

class TextBlock(HUDObject):
    def __init__(self, anchor, scale, y_offset, align, down, count, font, size, color=None):
        HUDObject.__init__(self, anchor, scale)
        if down:
            y_offset = -y_offset
        self.y_offset = y_offset
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

    def get_height(self):
        return self.scale[1] * self.size * self.count

    def set_font(self, font):
        self.font = font

    def update_instance(self):
        for i in range(self.count):
            if self.down:
                pos = -(i + 1)
            else:
                pos = i + 0.1
            self.instances[i].setPos(0, pos * self.scale[1] *self.size + self.y_offset)

    def set_y_offset(self, y_offset):
        if self.down:
            y_offset = -y_offset
        self.y_offset = y_offset
        self.update_instance()

    def create_line(self, i):
        if self.down:
            pos = -(i + 1)
        else:
            pos = i + 0.1
        return OnscreenText(text="",
                            style=Plain,
                            fg=self.color,
                            scale=tuple(self.scale * self.size),
                            parent=self.instance,
                            pos=(0, pos * self.scale[1] * self.size + self.y_offset),
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

class HUD():
    def __init__(self, scale, font):
        self.scale = scale
        self.font = font
        self.title = TextLine(base.a2dTopLeft, self.scale, 0, TextNode.ALeft, True, 0, self.font, settings.info_text_size, settings.hud_color)
        title_height = self.title.get_height()
        self.topLeft = TextBlock(base.a2dTopLeft, self.scale, title_height, TextNode.ALeft, True, 10, self.font, settings.hud_text_size)
        self.bottomLeft = TextBlock(base.a2dBottomLeft, self.scale, 0, TextNode.ALeft, False, 5, self.font, settings.hud_text_size)
        self.topRight = TextBlock(base.a2dTopRight, self.scale, 0, TextNode.ARight, True, 5, self.font, settings.hud_text_size)
        self.bottomRight = TextBlock(base.a2dBottomRight, self.scale, 0, TextNode.ARight, False, 5, self.font, settings.hud_text_size)
        #TODO: Info should be moved out of HUD
        self.info = FadeTextLine(base.a2dBottomLeft, self.scale, 0, TextNode.ALeft, False, 6, self.font, settings.info_text_size)
        self.shown = True

    def hide(self):
        self.title.hide()
        self.topLeft.hide()
        self.bottomLeft.hide()
        self.topRight.hide()
        self.bottomRight.hide()
        self.shown = False

    def show(self):
        self.title.show()
        self.topLeft.show()
        self.bottomLeft.show()
        self.topRight.show()
        self.bottomRight.show()
        self.shown = True

    def set_scale(self, scale):
        self.title.set_scale(scale)
        self.topLeft.set_scale(scale)
        self.bottomLeft.set_scale(scale)
        self.topRight.set_scale(scale)
        self.bottomRight.set_scale(scale)
        self.info.set_scale(scale)

    def set_y_offset(self, y_offset):
        self.title.set_y_offset(y_offset)
        title_height = self.title.get_height()
        self.topLeft.set_y_offset(y_offset + title_height)
        self.topRight.set_y_offset(y_offset)
