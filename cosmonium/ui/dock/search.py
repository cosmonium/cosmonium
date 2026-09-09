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
from direct.gui.DirectEntry import DirectEntry
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectGuiBase import DirectGuiWidget
from directguilayout.gui import Sizer
from directguilayout.gui import Widget as SizerWidget
from panda3d.core import TextNode

from ... import settings
from ...fonts import Font, fontsManager
from ..core.search import NameSearchController
from ..skin import UIElement, combine_classes
from .base import DGuiDockWidget

if TYPE_CHECKING:
    from .dock import Dock


class SearchDockWidget(DGuiDockWidget):
    """A dock widget with a name-entry box that shows a dropdown of the first matching objects."""

    element_type = 'entry'

    def __init__(self, placeholder: str = None, width: float = 12, max_results: int = 8, **kwargs):
        DGuiDockWidget.__init__(self, **kwargs)
        self.placeholder = placeholder
        self.placeholder_text = None
        self.width = width
        self.max_results = max_results
        self.dock = None
        self.entry = None
        self.panel = None
        self.result_buttons = []
        self.result_style = None
        self.result_font_bold = None
        self.result_gap = 0
        self.search = None

    def create(self, dock: Dock, parent, messenger, skin) -> DirectGuiWidget:
        self.dock = dock

        # Resolved here to be able to translate the text.
        self.placeholder_text = self.placeholder if self.placeholder is not None else _("Search...")

        entry_style = skin.get_style(self.element)
        self.entry = DirectEntry(
            initialText=self.placeholder_text,
            command=self.do_query,
            numLines=1,
            width=self.width,
            focus=0,
            suppressKeys=1,
            focusInCommand=self._on_focus_in,
            focusOutCommand=self._on_focus_out,
            **entry_style,
        )
        self.entry.bind("press-escape-", self.escape)
        self.entry.bind("press-arrow_up-", self.move_selection, extraArgs=[-1])
        self.entry.bind("press-arrow_down-", self.move_selection, extraArgs=[1])
        self.entry.accept(self.entry.guiItem.getTypeEvent(), self.completion)
        self.entry.accept(self.entry.guiItem.getEraseEvent(), self.completion)

        panel_element = UIElement('frame', class_=combine_classes('search-results', self.class_), parent=parent.element)
        result_element = UIElement(
            'button', class_=combine_classes('search-results', self.class_), parent=parent.element
        )
        self.result_style = skin.get_style(result_element)
        result_font_family = skin.get(result_element).font_family
        self.result_font_bold = fontsManager.load_font(result_font_family, Font.STYLE_BOLD) or self.result_style.get(
            'text_font'
        )
        self.result_gap = self.result_style['text_scale'][1] * 0.3
        self.panel = DirectFrame(parent=self.entry, **skin.get_style(panel_element))
        self.panel.hide()
        return self.entry

    def do_query(self, text):
        body = self.search.resolve(self.entry.get())
        if body is not None:
            builtins.base.gui.select_object(body)
        self._reset_to_default()

    def escape(self, event):
        self._reset_to_default()

    def select_result(self, body):
        builtins.base.gui.select_object(body)
        self._reset_to_default()

    def _reset_to_default(self):
        self.search.reset()
        self._clear_result_buttons()
        self.panel.hide()
        self.entry.set(self.placeholder_text)
        self.entry['focus'] = 0

    def _on_focus_in(self):
        if self.entry.get() == self.placeholder_text:
            self.entry.set('')
        if self.search is None:
            gui = builtins.base.gui
            self.search = NameSearchController(gui, settings.query_delay, self.update_results, self.max_results)

    def _on_focus_out(self):
        if self.entry.get() == '':
            self.entry.set(self.placeholder_text)

    def completion(self, event):
        self.search.update_query(self.entry.get())

    def move_selection(self, event, increment):
        self.search.move_selection(increment)

    def _clear_result_buttons(self):
        for button in self.result_buttons:
            button.destroy()
        self.result_buttons = []

    def update_results(self):
        current_list = self.search.current_list
        current_selection = self.search.current_selection

        self._clear_result_buttons()
        if not current_list:
            self.panel.hide()
            return

        sizer = Sizer("vertical", gaps=(0, self.result_gap))
        for i, (name, body) in enumerate(current_list):
            style = dict(self.result_style)
            if i == current_selection:
                style['text_font'] = self.result_font_bold
            button = DirectButton(
                text=name,
                text_align=TextNode.ALeft,
                relief=None,
                pressEffect=1,
                parent=self.panel,
                command=self.select_result,
                extraArgs=[body],
                **style,
            )
            self.result_buttons.append(button)
            sizer.add(SizerWidget(button), proportions=(1.0, 0.0), alignments=("expand", "min"))

        self._layout_panel(sizer)
        self.panel.show()

    def _layout_panel(self, sizer):
        entry_bounds = self.entry.getBounds()
        min_width, min_height = sizer.update_min_size()
        target_width = min_width
        if entry_bounds is not None:
            target_width = max(target_width, entry_bounds[1] - entry_bounds[0])
        sizer.update((target_width, min_height))
        panel_width, panel_height = sizer.get_size()
        self.panel['frameSize'] = (0, panel_width, -panel_height, 0)

        if entry_bounds is None:
            return
        left, right, bottom, top = entry_bounds
        pos = self.panel.get_pos(self.entry)
        if self.dock is not None and self.dock.location.startswith("bottom"):
            # Located at the bottom ofthe window, pop the results upward.
            pos.set_z(top + panel_height)
        else:
            pos.set_z(bottom)
        self.panel.set_pos(self.entry, pos)
