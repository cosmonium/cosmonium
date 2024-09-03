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
from panda3d.core import LVector3

from ...fonts import fontsManager, Font
from ..skin import UIElement
from .base import DGuiDockWidget


class TextDockWidget(DGuiDockWidget):

    font = None

    def __init__(
            self,
            text: str,
            data: str,
            align,
            size: float=None,
            proportions=None,
            alignments=None,
            borders=None,
            index=None):
        DGuiDockWidget.__init__(self, proportions, alignments, borders, index)
        if data is not None:
            self.data = data
            # TODO: A non empty text is needed to retrieve a valid frameSize
            self.text = "M"
            self.frame_size = None
            self.update_needed = True
        else:
            self.data = None
            self.text = text
            self.frame_size = None
        self.size = size
        self.align = align
        if self.font is None:
            font = fontsManager.get_font("DejaVuSans", Font.STYLE_NORMAL)
            TextDockWidget.font = font.load()

    def create(self, dock: Dock, parent, messenger, skin) -> DirectGuiWidget:
        label_element = UIElement('label', parent=parent.element)
        scale = LVector3(self.size or parent.size)
        label = DirectLabel(
            **skin.get_style(label_element),
            text=self.text,
            text_font=self.font,
            scale=scale,
            text_align=self.align,
            frameSize=self.frame_size,
            textMayChange=True)
        if self.data is not None:
            bounds = label.getBounds()
            label['frameSize'] = (0, 15, bounds[2], bounds[3])
        return label

    def update(self):
        has_changed = False
        if self.data is not None:
            text = base.data_provider.get_data(self.data)
            if text != self.text:
                self.widget.dgui_obj['text'] = text
                self.widget.reset_frame_size()
                self.text = text
                has_changed = True
        return has_changed
