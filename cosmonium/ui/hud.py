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

from panda3d.core import TextNode, LColor, LVector2, LVector3

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
        self.instance.stash()
        self.shown = False

    def show(self):
        self.instance.unstash()
        self.shown = True

    def set_scale(self, scale):
        self.scale = scale
        self.update_instance()

class TextLine(HUDObject):
    def __init__(self, anchor, scale, offset, align, pos, font, size, color=None):
        HUDObject.__init__(self, anchor, scale)
        self.offset = offset
        self.align = align
        self.text = ""
        self.instance = None
        self.font = font
        self.size = size
        self.pos = LVector2(pos[0], -pos[1])
        if color is None:
            color = LColor(1, 1, 1, 1)
        self.color = color
        self.instance = self.create()
        self.update_instance()

    def get_em_width(self):
        return self.scale[0] * self.size

    def get_height(self):
        return self.scale[1] * self.size

    def set_font(self, font):
        self.font = font

    def update_instance(self):
        if self.instance is None: return
        x_offset = self.offset[0]
        y_offset = self.offset[1]
        pos = LVector3(self.pos[0] * self.get_em_width() + x_offset, 0, self.pos[1] * self.get_height() + y_offset)
        #self.instance.setScale(*self.scale)
        self.instance.set_pos(pos)

    def set_offset(self, offset):
        self.offset = offset
        self.update_instance()

    def set_pos(self, pos):
        self.pos = (pos[0], -pos[1])
        self.update_instance()

    def set_parent(self, parent):
        if parent != self.anchor:
            self.anchor = parent
            self.instance.reparent_to(self.anchor)

    def create(self):
        return OnscreenText(text="",
                            style=Plain,
                            fg=self.color,
                            scale=tuple(self.scale * self.size),
                            parent=self.anchor,
                            align=self.align,
                            font=self.font,
                            mayChange=True)

    def set_text(self, text):
        self.instance.setText(text)
        self.text = text

    def set_all(self, text, pos, anchor):
        self.set_text(text)
        self.set_parent(anchor)
        self.set_pos(pos)

class FadeTextLine(TextLine):
    def __init__(self, *args, **kwargs):
        TextLine.__init__(self, *args, **kwargs)
        self.fade_sequence = None

    def set(self, text, pos, color, anchor, duration, fade):
        if anchor is None:
            anchor = base.a2dBottomLeft
        TextLine.set_all(self, text, pos, anchor)
        self.instance.setColorScale(LColor(*color))
        if self.fade_sequence is not None:
            self.fade_sequence.pause()
        self.fade_sequence = Sequence(Wait(duration),
                                      self.instance.colorScaleInterval(fade, LColor(1, 1, 1, 0)))
        self.fade_sequence.start()

class TextBlock(HUDObject):
    def __init__(self, anchor, scale, offset, align, down, count, font, size, color=None):
        HUDObject.__init__(self, anchor, scale)
        self.offset = offset
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

    def set_offset(self, offset):
        self.offset = offset
        self.update_instance()

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

class HUD():
    def __init__(self, scale, font):
        self.scale = scale
        self.font = font
        offset = LVector2()
        self.title = TextLine(base.a2dTopLeft, self.scale, offset, TextNode.ALeft, LVector2(0, 1), self.font, settings.hud_info_text_size, settings.hud_color)
        title_height = self.title.get_height()
        self.topLeft = TextBlock(base.a2dTopLeft, self.scale, LVector2(0, title_height), TextNode.ALeft, True, 10, self.font, settings.hud_text_size)
        self.bottomLeft = TextBlock(base.a2dBottomLeft, self.scale, offset, TextNode.ALeft, False, 5, self.font, settings.hud_text_size)
        self.topRight = TextBlock(base.a2dTopRight, self.scale, offset, TextNode.ARight, True, 5, self.font, settings.hud_text_size)
        self.bottomRight = TextBlock(base.a2dBottomRight, self.scale, offset, TextNode.ARight, False, 5, self.font, settings.hud_text_size)
        #TODO: Info should be moved out of HUD
        self.info = FadeTextLine(base.a2dBottomLeft, self.scale, offset, TextNode.ALeft, LVector2(0, -3), self.font, settings.hud_info_text_size)
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
        self.title.set_offset((0, -y_offset))
        title_height = self.title.get_height()
        self.topLeft.set_offset((0, y_offset + title_height))
        self.topRight.set_offset((0, y_offset))
