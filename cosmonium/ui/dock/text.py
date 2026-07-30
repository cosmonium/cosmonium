#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2026 Laurent Deru.
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

from typing import TYPE_CHECKING

from direct.gui.DirectGuiBase import DirectGuiWidget
from direct.gui.DirectLabel import DirectLabel

from ..skin import UIElement
from .base import DGuiDockWidget

if TYPE_CHECKING:
    from .dock import Dock


class TextDockWidget(DGuiDockWidget):

    def __init__(self, template: str, align, proportions=None, alignments=None, borders=None, index=None):
        DGuiDockWidget.__init__(self, proportions, alignments, borders, index)
        self.align = align
        self.template = template
        self.text = None

    def create(self, dock: Dock, parent, messenger, skin) -> DirectGuiWidget:
        label_element = UIElement('label', parent=parent.element)
        self.text = ""
        label = DirectLabel(**skin.get_style(label_element), text=self.text, text_align=self.align, textMayChange=True)
        return label

    def update(self, global_vars):
        has_changed = False
        text = self.template.render(global_vars)
        if text != self.text:
            self.widget.dgui_obj['text'] = text
            self.widget.reset_frame_size()
            self.text = text
            has_changed = True
        return has_changed
