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

from __future__ import annotations

from direct.gui.DirectGuiBase import DirectGuiWidget
from direct.gui.DirectLabel import DirectLabel

from ..skin import UIElement
from .base import DGuiDockWidget


class TextDockWidget(DGuiDockWidget):

    def __init__(self, text: str, align, proportions=None, alignments=None, borders=None, index=None):
        DGuiDockWidget.__init__(self, proportions, alignments, borders, index)
        self.text_source = text
        self.align = align
        self.template = None
        self.text = None

    def compile(self, env):
        self.template = env.create_template(self.text_source)

    def create(self, dock: Dock, parent, messenger, skin) -> DirectGuiWidget:
        label_element = UIElement('label', parent=parent.element)
        self.text = self.template.render()
        label = DirectLabel(**skin.get_style(label_element), text=self.text, text_align=self.align, textMayChange=True)
        return label

    def update(self):
        has_changed = False
        text = self.template.render()
        if text != self.text:
            self.widget.dgui_obj['text'] = text
            self.widget.reset_frame_size()
            self.text = text
            has_changed = True
        return has_changed
