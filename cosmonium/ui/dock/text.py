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
from panda3d.core import TextNode

from ..skin import UISkin
from .base import DGuiDockWidget

if TYPE_CHECKING:
    from .dock import Dock


class TextDockWidget(DGuiDockWidget):
    """A dock widget displaying a line of text, rendered from a template."""

    element_type = 'label'

    def __init__(self, template: str, text_align: int = None, **kwargs):
        """
        Args:
            template: The template rendered into the displayed text
            text_align: Alignment of the text inside the widget, overriding the skin, or None
            kwargs: The layout parameters common to every dock widget, see `DockWidgetBase`
        """
        DGuiDockWidget.__init__(self, **kwargs)
        self.text_align = text_align
        self.template = template
        self.text_align = text_align
        self.text = None

    def create(self, dock: Dock, parent, messenger, skin: UISkin) -> DirectGuiWidget:
        style = skin.get_style(self.element)
        if self.text_align is not None:
            style['text_align'] = self.text_align
        # Text align to the left unless the skin or the widget configuration says otherwise
        style.setdefault('text_align', TextNode.A_boxed_left)
        self.text = ""
        label = DirectLabel(**style, text=self.text, textMayChange=True)
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
