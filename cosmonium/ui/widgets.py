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


from panda3d.core import TextNode
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DGG
from direct.gui.DirectScrolledFrame import DirectScrolledFrame

class DirectWidgetContainer():
    def __init__(self, widget):
        self.frame = widget

    def destroy(self):
        self.frame.destroy()

    def reparent_to(self, parent):
        self.frame.reparent_to(parent)

class ScrollText():
    def __init__(self, text='', align=TextNode.ALeft, scale=(1, 1), font=None, font_size=12,
                 parent=None,
                 frameColor=(0.33, 0.33, 0.33, .66), frameSize=(0, 0.5, -1.0, 0)):
        if parent is None:
            parent = aspect2d
        self.parent = parent
        self.frame = DirectScrolledFrame(parent=parent, frameColor=frameColor, state=DGG.DISABLED,
                                         frameSize=frameSize,
                                         relief=DGG.FLAT,
                                         scrollBarWidth=scale[0] * font_size,
                                         horizontalScroll_relief=DGG.FLAT,
                                         verticalScroll_relief=DGG.FLAT,
                                         )
        self.text = OnscreenText(parent=self.frame.getCanvas(),
                                 text=text,
                                 align=align,
                                 scale=tuple(scale * font_size),
                                 font=font)
        bounds = self.text.getTightBounds()
        self.frame['canvasSize'] = [0, bounds[1][0] - bounds[0][0], -bounds[1][2] + bounds[0][2], 0]
        self.text.setPos(-bounds[0][0], -bounds[1][2])
        self.frame.setPos(0, 0, 0)

    def destroy(self):
        self.frame.destroy()

    def reparent_to(self, parent):
        self.frame.reparent_to(parent)
