#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
#
# Cosmonium is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Cosmonium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#


from panda3d.core import TextNode

from ...dircontext import defaultDirContext
from ..markdown import create_markdown_renderer
from ..skin import UIElement
from ..widgets.scroll_text import ScrollText
from ..widgets.window import Window
from .uiwindow import UIWindow


class TextWindow(UIWindow):
    def __init__(self, title, owner=None):
        UIWindow.__init__(self, owner)
        self.title = title
        self.element = UIElement('text-window')
        self.markdown = create_markdown_renderer(self.skin.get(self.element).font_family)

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
        self.layout = ScrollText(parent=self.owner.root, text=self.text, align=TextNode.ALeft, owner=self)
        self.window = Window(self.title, scale=self.scale, child=self.layout, owner=self)
        self.window.register_scroller(self.layout.frame)
