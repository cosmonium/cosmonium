# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import TextNode

from ..dircontext import defaultDirContext

from .window import Window
from .markdown import create_markdown_renderer
from .widgets import ScrollText

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
