#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2024 Laurent Deru.
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


from panda3d.core import TextNode
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DGG
from direct.gui.DirectScrolledFrame import DirectScrolledFrame

from .direct_widget_container import DirectWidgetContainer
from ..skin import UIElement


class ScrollText(DirectWidgetContainer):
    def __init__(self, text='', align=TextNode.ALeft,
                 parent=None,
                 frameSize=(0, 800, -600, 0),
                 owner=None):
        super().__init__(None)
        self.parent = parent
        self.owner = owner
        self.skin = owner.skin
        scrolled_frame_element = UIElement('scrolled-frame', class_='scroll-text')
        self.frame = DirectScrolledFrame(
            parent=parent,
            state=DGG.DISABLED,
            frameSize=frameSize,
            relief=DGG.FLAT,
            horizontalScroll_relief=DGG.FLAT,
            verticalScroll_relief=DGG.FLAT,
            **self.skin.get_style(scrolled_frame_element)
            )
        text_element = UIElement('onscreen-text', parent=scrolled_frame_element)
        self.text = OnscreenText(
            parent=self.frame.getCanvas(),
            text=text,
            align=align,
            **self.skin.get_style(text_element))
        bounds = self.text.getTightBounds()
        self.frame['canvasSize'] = [0, bounds[1][0] - bounds[0][0], -bounds[1][2] + bounds[0][2], 0]
        self.text.setPos(-bounds[0][0], -bounds[1][2])
