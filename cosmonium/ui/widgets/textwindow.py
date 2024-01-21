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


from panda3d.core import LVector2, TextNode

from ...dircontext import defaultDirContext
from ... import settings
from ..markdown import create_markdown_renderer

from .scroll_text import ScrollText
from .window import Window


class TextWindow():
    def __init__(self, title, font_family, font_size = 14, owner=None):
        self.title = title
        self.window = None
        self.layout = None
        self.last_pos = None
        self.font_size = font_size
        self.owner = owner
        self.scale = LVector2(settings.ui_scale, settings.ui_scale)
        self.text_scale = (self.font_size * settings.ui_scale, self.font_size * settings.ui_scale)
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
        self.layout = ScrollText(
            parent=pixel2d,
            text=self.text,
            align=TextNode.ALeft,
            scale=self.text_scale,
            font=self.markdown.renderer.font_normal,
            font_size=self.font_size)
        self.window = Window(self.title, scale=self.scale, child=self.layout, owner=self)
        self.window.register_scroller(self.layout.frame)

    def show(self):
        self.create_layout()
        if self.last_pos is None:
            if self.owner is not None:
                width = self.layout.frame['frameSize'][1] - self.layout.frame['frameSize'][0]
                height = self.layout.frame['frameSize'][3] - self.layout.frame['frameSize'][2]
                self.last_pos = ((self.owner.width - width) / 2, 0, -(self.owner.height - height) / 2)
            else:
                self.last_pos = (100, 0, -100)
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
