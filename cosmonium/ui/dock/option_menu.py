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
from direct.gui.DirectOptionMenu import DirectOptionMenu
from panda3d.core import TextNode

from ..skin import UISkin
from .base import DGuiDockWidget

if TYPE_CHECKING:
    from .dock import Dock


class _DockOptionMenu(DirectOptionMenu):
    """A DirectOptionMenu that pops its item list towards the dock's free side.

    A dock anchored to a screen edge only has room to grow away from that edge: a dock at the
    bottom of the screen must pop its list upward, one at the right edge must pop it leftward,
    and so on. This subclass overrides `showPopupMenu` to use the best position.
    """

    def __init__(self, dock: Dock, **kw):
        DirectOptionMenu.__init__(self, **kw)
        self._dock = dock
        self.initialiseoptions(_DockOptionMenu)

    def showPopupMenu(self, event=None):
        DirectOptionMenu.showPopupMenu(self, event)
        self._reposition_popup()

    def _reposition_popup(self):
        frame_size = self.popupMenu['frameSize']
        button_bounds = self.getBounds()
        if frame_size is None or button_bounds is None:
            return
        left, right, bottom, top = frame_size
        pos = self.popupMenu.get_pos(self)
        if self._dock.direction == "horizontal":
            # A horizontal dock sits at the top or bottom of the screen: flip the list upward
            # when the dock is at the bottom so it doesn't spill off-screen.
            if self._dock.location.startswith("bottom"):
                pos.set_z(button_bounds[3] - bottom)
        else:
            # A vertical dock sits at the left or right of the screen: flip the list towards
            # the screen's center so it doesn't spill off-screen.
            if self._dock.location.endswith("right"):
                pos.set_x(button_bounds[0] - right)
            elif self._dock.location.endswith("left"):
                pos.set_x(button_bounds[1] - left)
        self.popupMenu.set_pos(self, pos)


class OptionMenuDockWidget(DGuiDockWidget):
    """A dock widget showing a drop-down list of options."""

    element_type = 'option-menu'

    def __init__(self, items: list[str], event: str, selected=None, **kwargs):
        """
        Args:
            items: The selectable options
            event: The event sent, with the selected option, when the selection changes
            selected: Callable returning the initially selected option, or None
            kwargs: The layout parameters common to every dock widget, see `DockWidgetBase`
        """
        DGuiDockWidget.__init__(self, **kwargs)
        self.items = items
        self.event = event
        # Note: selected is a callable that returns the currently selected item.
        # But currenlt it is only called at creation time, so it won't update the selection if the value changes later.
        self.selected = selected

    def create(self, dock: Dock, parent, messenger, skin: UISkin) -> DirectGuiWidget:
        initial_item = self.items[0]
        if self.selected is not None:
            value = self.selected()
            if value in self.items:
                initial_item = value
        style = skin.get_style(self.element)
        # The selected option and the entries of the list read from the left unless the skin says otherwise
        style.setdefault('text_align', TextNode.A_left)
        style.setdefault('item_text_align', TextNode.A_left)
        option_menu = _DockOptionMenu(
            dock,
            **style,
            relief=None,
            items=self.items,
            initialitem=initial_item,
            textMayChange=True,
            command=lambda selection: messenger.send(self.event, [selection]),
        )
        return option_menu
