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

from direct.gui.DirectButton import DirectButton
from direct.gui.DirectGuiBase import DirectGuiWidget

from panda3d.core import LVector3, TextNode

from ...fonts import fontsManager, Font
from ..skin import UIElement
from .base import DGuiDockWidget


class ButtonDockWidget(DGuiDockWidget):

    font = None

    def __init__(
            self,
            text: str,
            event: str,
            size: float=None,
            rescale: bool=False,
            proportions=None,
            alignments=None,
            borders=None,
            index=None):
        DGuiDockWidget.__init__(self, proportions, alignments, borders, index)
        self.text = text
        self.event = event
        self.size = size
        if self.font is None:
            font = fontsManager.get_font("Material Design Icons", Font.STYLE_NORMAL)
            ButtonDockWidget.font = font.load()
            ButtonDockWidget.font.set_pixels_per_unit(64)
        self.rescale = rescale

    def create(self, dock: Dock, parent, messenger, skin) -> DirectGuiWidget:
        button_element = UIElement('button', parent=parent.element)
        size = self.size or parent.size
        scale = LVector3(size)
        button = DirectButton(
            **skin.get_style(button_element),
            relief=None,
            pressEffect=1,
            text_font=self.font,
            text=self.text,
            textMayChange=True,
            text_align=TextNode.A_boxed_center,
            scale=scale,
            command=messenger.send,
            extraArgs=[self.event])
        bounds = button.getBounds()
        if self.rescale and bounds is not None:
            width = bounds[1] - bounds[0]
            height = bounds[3] - bounds[2]
            max_size = max(width, height)
            button.set_scale(scale / max_size)
        return button
