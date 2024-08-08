#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2024 Laurent Deru.
#
#Cosmonium is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Cosmonium is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#


from panda3d.core import KeyboardButton, TextNode
from direct.gui.DirectGui import DirectEntry
from direct.gui.DirectFrame import DirectFrame
from direct.gui.OnscreenText import OnscreenText
from direct.task.TaskManagerGlobal import taskMgr

from ..skin import UIElement

from .hud_object import HUDObject


class Query(HUDObject):
    def __init__(self, id_, anchor, offset, query_delay, owner=None):
        HUDObject.__init__(self, id_, owner)
        self.query_delay = query_delay
        self.background = None
        self.prefix = None
        self.query = None
        self.suggestions = None
        self.current_selection = None
        self.current_list = []
        self.completion_task = None
        self.max_columns = 4
        self.max_lines = 3
        self.max_elems = self.max_columns * self.max_lines
        self.set_anchor(anchor)
        self.offset = offset

    def do_query(self, text):
        body = None
        if self.current_selection is not None:
            if self.current_selection < len(self.current_list):
                body = self.current_list[self.current_selection][1]
        else:
            text = self.query.get()
            body = self.owner.get_object(text)
        self.owner.select_object(body)
        self.close()

    def close(self):
        self.background.destroy()
        self.background = None
        self.prefix.destroy()
        self.prefix = None
        self.query.destroy()
        self.query = None
        self.suggestions.destroy()
        self.suggestions = None
        self.current_selection = None
        self.current_list = []
        if self.completion_task is not None:
            taskMgr.remove(self.completion_task)
            self.completion_task = None

    def escape(self, event):
        self.close()

    def update_suggestions(self):
        if self.current_selection is not None:
            page = self.current_selection // self.max_elems
        else:
            page = 0
        start = page * self.max_elems
        end = min(start + self.max_elems - 1, len(self.current_list) - 1)
        suggestions = ""
        for i in range(start, end + 1):
            if i != start and ((i - start) % self.max_columns) == 0:
                suggestions += '\n'
            if i == self.current_selection:
                suggestions += "\1md_bold\1%s\2" % self.current_list[i][0]
            else:
                suggestions += self.current_list[i][0]
            suggestions += '\t'
        self.suggestions.setText(suggestions)

    def completion(self, event):
        text = self.query.get()
        if text != '':
            self.current_list = self.owner.list_objects(text)
        else:
            self.current_list = []
        self.current_selection = None
        if self.completion_task is not None:
            taskMgr.remove(self.completion_task)
        self.completion_task = taskMgr.doMethodLater(
            self.query_delay, self.update_suggestions, 'completion task', extraArgs=[])

    def select(self, event):
        modifiers = event.getModifierButtons()
        if modifiers.isDown(KeyboardButton.shift()):
            incr = -1
        else:
            incr = 1
        if self.current_selection is not None:
            new_selection = self.current_selection + incr
        else:
            new_selection = 0
        if new_selection < 0:
            new_selection = len(self.current_list) - 1
        if new_selection >= len(self.current_list):
            new_selection = 0
        self.current_selection = new_selection
        self.update_suggestions()

    def open_query(self, owner):
        self.owner = owner
        element = UIElement(None, id_=self.id_)
        background_element = UIElement('frame', parent=element)
        text_element = UIElement('onscreen-text', parent=element, class_='query-entry')
        query_element = UIElement('entry', parent=element, class_='query-entry')
        query_style = self.skin.get_style(query_element)
        query_height = query_style['text_scale'][1]
        suggestion_element = UIElement('onscreen-text', parent=element, id_='query-suggestion')
        suggestion_style = self.skin.get_style(suggestion_element)
        suggestion_height = suggestion_style['scale'][1] * (self.max_lines + 1) * 1.5
        suggestion_offset = suggestion_style['scale'][1] * self.max_lines * 1.5
        self.background = DirectFrame(
            frameSize=(0, self.owner.width, query_height + suggestion_height, 0.0),
            parent=self.anchor,
            **self.skin.get_style(background_element))
        self.prefix = OnscreenText(
            text=_("Target name: "),
            align=TextNode.ALeft,
            parent=self.anchor,
            pos=(0, suggestion_height),
            **self.skin.get_style(text_element))
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
            **query_style)
        self.query.bind("press-escape-", self.escape)
        self.query.bind("press-tab-", self.select)
        self.query.accept(self.query.guiItem.getTypeEvent(), self.completion)
        self.query.accept(self.query.guiItem.getEraseEvent(), self.completion)
        bounds = self.query.getBounds()
        self.suggestions = OnscreenText(
            text="",
            align=TextNode.ALeft,
            mayChange=True,
            parent=self.anchor,
            pos=(0, suggestion_offset),
            **suggestion_style)
