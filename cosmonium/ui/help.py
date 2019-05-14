# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import TextNode
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DGG
from direct.gui.DirectScrolledFrame import DirectScrolledFrame

from .window import Window
from .markdown import create_markdown_renderer

import os
from cosmonium.dircontext import defaultDirContext

class ScrollText():
    def __init__(self, text='', align=TextNode.ALeft, scale=(1, 1), font=None, font_size=12, parent=None, frameColor=(0.33, 0.33, 0.33, .66)):
        if parent is None:
            parent = aspect2d
        self.parent = parent
        self.frame = DirectScrolledFrame(parent=parent, frameColor=frameColor, state=DGG.DISABLED,
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
        self.frame['frameSize'] = [0, 0.5, -0.5, 0]
        print(self.frame['frameSize'],  -bounds[1][2])
        self.text.setPos(-bounds[0][0], -bounds[1][2])
        self.frame.setPos(0, 0, 0)

    def destroy(self):
        self.frame.destroy()

    def reparent_to(self, parent):
        self.frame.reparent_to(parent)

class HelpPanel():
    def __init__(self, scale, font_family, font_size = 14):
        self.window = None
        self.layout = None
        self.last_pos = None
        self.scale = scale
        self.font_size = font_size
        filename = defaultDirContext.find_doc('control.md')
        with open(filename) as help_file:
            self.help_text = ''.join(help_file.readlines())
        self.markdown = create_markdown_renderer(font_family)

    def create_layout(self):
        self.layout = ScrollText(text=self.markdown(self.help_text),
                                 align=TextNode.ALeft,
                                 scale=self.scale,
                                 font=self.markdown.renderer.font_normal,
                                 font_size=self.font_size)
        title = "Help"
        self.window = Window(title, scale=self.scale, child=self.layout, owner=self, transparent=True)

    def show(self):
        self.create_layout()
        if self.last_pos is None:
            self.last_pos = (-self.layout.frame['frameSize'][1] / 2, 0, -self.layout.frame['frameSize'][2] / 2)
        self.window.setPos(self.last_pos)
        self.window.update()

    def hide(self):
        if self.window is not None:
            self.last_pos = self.window.getPos()
            self.window.destroy()
            self.window = None
            self.layout = None

    def shown(self):
        return self.window is not None

    def window_closed(self, window):
        if window is self.window:
            self.last_pos = self.window.getPos()
            self.window = None
            self.layout = None
