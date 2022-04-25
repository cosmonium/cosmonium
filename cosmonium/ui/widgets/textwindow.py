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


from panda3d.core import TextNode

from ...dircontext import defaultDirContext

from .window import Window
from ..markdown import create_markdown_renderer
from .scroll_text import ScrollText


class TextWindow():
    def __init__(self, title, scale, font_family, font_size = 14, owner=None):
        self.title = title
        self.window = None
        self.layout = None
        self.last_pos = None
        self.scale = scale
        self.font_size = font_size
        self.owner = owner
        self.markdown = create_markdown_renderer(font_family)

    def load(self, filename, markdown=True):
        filename = defaultDirContext.find_doc(filename)
        with open(filename) as text_file:
            self.text = ''.join(text_file.readlines())
        if markdown:
            self.text = self.markdown(self.text)

    def set_text(self, text, markdown=True):
        self.text = text
        if markdown:
            self.text = self.markdown(self.text)

    def create_layout(self):
        self.layout = ScrollText(text=self.text,
                                 align=TextNode.ALeft,
                                 scale=self.scale,
                                 font=self.markdown.renderer.font_normal,
                                 font_size=self.font_size)
        self.window = Window(self.title, scale=self.scale, child=self.layout, owner=self, transparent=True)
        self.window.register_scroller(self.layout.frame)

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
            if self.owner is not None:
                self.owner.window_closed(self)
