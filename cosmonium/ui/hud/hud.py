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


from panda3d.core import TextNode, LVector2

from ... import settings

from .fadetextline import FadeTextLine
from .textblock import TextBlock
from .textline import TextLine


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
