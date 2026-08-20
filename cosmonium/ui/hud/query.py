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


from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectGui import DirectEntry
from direct.gui.DirectLabel import DirectLabel
from direct.gui.OnscreenText import OnscreenText
from directguilayout.gui import Sizer
from directguilayout.gui import Widget as SizerWidget
from panda3d.core import KeyboardButton, TextNode

from ...fonts import Font, fontsManager
from ..core.search import NameSearchController
from ..core.ui_element import OverlayUIElement
from ..skin import UIElement


class Query(OverlayUIElement):
    def __init__(self, id_, anchor, offset, query_delay, parent=None):
        OverlayUIElement.__init__(self, id_, parent=parent)
        self.query_delay = query_delay
        self.background = None
        self.prefix = None
        self.query = None
        self.suggestions_root = None
        self.suggestion_labels = []
        self.suggestion_style = None
        self.suggestion_font_bold = None
        self.suggestion_gaps = (0, 0)
        self.search = None
        self.max_columns = 4
        self.max_lines = 3
        self.max_elems = self.max_columns * self.max_lines
        self.set_anchor(anchor)
        self.offset = offset

    def do_query(self, text):
        body = self.search.resolve(self.query.get())
        self.parent.select_object(body)
        self.close()

    def close(self):
        self.background.destroy()
        self.background = None
        self.prefix.destroy()
        self.prefix = None
        self.query.destroy()
        self.query = None
        self.clear_suggestion_labels()
        self.suggestions_root.remove_node()
        self.suggestions_root = None
        self.search.reset()
        self.search = None

    def escape(self, event):
        self.close()

    def clear_suggestion_labels(self):
        for label in self.suggestion_labels:
            label.destroy()
        self.suggestion_labels = []

    def update_suggestions(self):
        current_list = self.search.current_list
        current_selection = self.search.current_selection
        if current_selection is not None:
            page = current_selection // self.max_elems
        else:
            page = 0
        start = page * self.max_elems
        end = min(start + self.max_elems - 1, len(current_list) - 1)

        self.clear_suggestion_labels()
        if end < start:
            return

        unselected_style = self.suggestion_style
        selected_style = dict(self.suggestion_style)
        selected_style['text_font'] = self.suggestion_font_bold

        sizer = Sizer("horizontal", prim_limit=self.max_columns, gaps=self.suggestion_gaps)
        for i in range(start, end + 1):
            if i == current_selection:
                style = selected_style
            else:
                style = unselected_style
            label = DirectLabel(
                text=current_list[i][0],
                text_align=TextNode.ALeft,
                parent=self.suggestions_root,
                **style,
            )
            self.suggestion_labels.append(label)
            sizer.add(SizerWidget(label), alignments=("min", "min"))
        min_size = sizer.update_min_size()
        sizer.update(min_size)

    def completion(self, event):
        self.search.update_query(self.query.get())

    def select(self, event):
        modifiers = event.getModifierButtons()
        if modifiers.isDown(KeyboardButton.shift()):
            increment = -1
        else:
            increment = 1
        self.search.move_selection(increment)

    def create(self):
        element = UIElement(None, id_=self.id_)
        self.search = NameSearchController(self.parent, self.query_delay, self.update_suggestions)

        background_element = UIElement('frame', parent=element)
        text_element = UIElement('onscreen-text', parent=element, class_='query-entry')
        query_element = UIElement('entry', parent=element, class_='query-entry')
        query_style = self.skin.get_style(query_element)
        query_height = query_style['text_scale'][1]
        suggestion_element = UIElement('label', parent=element, id_='query-suggestion')
        # TODO: Selected style should be a separate element or state in the skin,.
        self.suggestion_style = self.skin.get_style(suggestion_element)
        suggestion_font_family = self.skin.get(suggestion_element).font_family
        self.suggestion_font_bold = fontsManager.load_font(
            suggestion_font_family, Font.STYLE_BOLD
        ) or self.suggestion_style.get('text_font')
        line_height = self.suggestion_style['text_scale'][1]
        self.suggestion_gaps = (line_height, line_height * 0.4)
        suggestion_height = line_height * (self.max_lines) * 1.5
        self.background = DirectFrame(
            frameSize=(0, self.parent.width, query_height + suggestion_height, 0.0),
            parent=self.anchor,
            **self.skin.get_style(background_element),
        )
        self.prefix = OnscreenText(
            text=_("Target name: "),
            align=TextNode.ALeft,
            parent=self.anchor,
            pos=(0, suggestion_height),
            **self.skin.get_style(text_element),
        )
        bounds = self.prefix.getTightBounds()
        length = bounds[1][0] - bounds[0][0]
        self.query = DirectEntry(
            text="",
            command=self.do_query,
            parent=self.anchor,
            pos=(length, 0, suggestion_height),
            initialText="",
            numLines=1,
            width=200,
            focus=1,
            suppressKeys=1,
            **query_style,
        )
        self.query.bind("press-escape-", self.escape)
        self.query.bind("press-tab-", self.select)
        self.query.accept(self.query.guiItem.getTypeEvent(), self.completion)
        self.query.accept(self.query.guiItem.getEraseEvent(), self.completion)
        self.suggestions_root = self.anchor.attach_new_node('query-suggestions')
        self.suggestions_root.set_pos(0, 0, suggestion_height - line_height * 0.5)

    def update_instance(self):
        # Nothing to update
        pass
