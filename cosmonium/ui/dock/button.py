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

import builtins
from typing import TYPE_CHECKING

from direct.gui.DirectButton import DirectButton
from direct.gui.DirectGuiBase import DirectGuiWidget
from panda3d.core import LVector3, TextNode

from ..skin import UIElement
from .base import DGuiDockWidget

if TYPE_CHECKING:
    from .dock import Dock


class ButtonDockWidget(DGuiDockWidget):

    def __init__(
        self,
        text: str,
        event: str,
        menu: str = None,
        size: float = None,
        rescale: bool = False,
        proportions=None,
        alignments=None,
        borders=None,
        index=None,
    ):
        DGuiDockWidget.__init__(self, proportions, alignments, borders, index)
        self.text = text
        self.event = event
        self.menu = menu
        self.size = size
        self.rescale = rescale

    def _open_menu(self):
        builtins.base.gui.open_named_menu(self.menu)

    def create(self, dock: Dock, parent, messenger, skin) -> DirectGuiWidget:
        button_element = UIElement('button', class_='dock-button', parent=parent.element)
        style = skin.get(button_element)
        size = self.size or parent.size
        font_size = style.font_size(button_element, True, skin)
        scale = LVector3(size / font_size)
        if self.menu is not None:
            command = self._open_menu
            extra_args = []
        else:
            command = messenger.send
            extra_args = [self.event]
        button = DirectButton(
            **skin.get_style(button_element),
            relief=None,
            pressEffect=1,
            text=self.text,
            textMayChange=True,
            text_align=TextNode.A_boxed_center,
            scale=scale,
            command=command,
            extraArgs=extra_args,
        )
        bounds = button.getBounds()
        if self.rescale and bounds is not None:
            width = bounds[1] - bounds[0]
            height = bounds[3] - bounds[2]
            max_size = max(width, height)
            button.set_scale(scale * font_size / max_size)
        return button
