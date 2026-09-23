# -*- coding: utf-8 -*-
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

import sys
from collections import defaultdict

from direct.showbase.DirectObject import DirectObject

from ..events import APPLICATION_WIDE_EVENTS


def remap_key_for_platform(key):
    """
    Remap a generic key combination read from a shortcuts file to the actual key
    combination bound at runtime on the current platform.

    Used both when binding shortcuts and when generating the control help
    document, so the displayed keys always match what is actually bound.
    """
    if sys.platform == 'darwin':
        key = key.replace('control', 'meta')
        if key == 'f11':
            key = 'shift-f11'
    return key


class Shortcuts(DirectObject):

    def __init__(self, base, messenger, gui):
        DirectObject.__init__(self)
        self.messenger = messenger
        self.gui = gui
        self.eventmap = defaultdict(lambda: [])
        self.keystrokes = {}
        # Active widgets that have been bound to application-wide shortcuts, and the list of events bound on each.
        self.widget_bindings = {}
        if not base.app_config.test_start:
            base.buttonThrowers[0].node().set_keystroke_event('keystroke')
        self.accept('keystroke', self.keystroke_event)

    def add_key(self, event, key, args=[]):
        key = remap_key_for_platform(key)
        self.eventmap[event].append(key)
        self.accept(key, self.messenger.send, [event, args])

    def set_shortcuts(self, categories):
        for category in categories:
            for shortcut in category.shortcuts:
                for key in shortcut.keys:
                    if isinstance(key, str):
                        self.add_key(shortcut.event, key, shortcut.args)
                    else:
                        self.add_key(shortcut.event, key.key, key.args or shortcut.args)

    def get_shortcuts_for(self, event):
        return self.eventmap.get(event, None)

    def bind_widget(self, widget):
        """
        Bind every application-wide shortcut directly on `widget`.

        A widget that suppresses keyboard events while it has focus stops the raw key events from ever
        # reaching this object. So we bind application-wide shortcuts on the widget to keep them working.
        # Must be paired with a call to unbind_widget() when the widget loses focus or is destroyed.

        Note: PGItem own press event is named after the plain key only, without any modifier prefix.
        So shortcuts are grouped by their plain button, and the actual modifiers held are checked against
        each candidate shortcut in _dispatch_widget_press().
        """
        by_button = {}
        for event in APPLICATION_WIDE_EVENTS:
            for shortcut in self.eventmap.get(event, []):
                button = shortcut.rsplit('-', 1)[-1]
                by_button.setdefault(button, []).append((shortcut, event))

        bindings = []
        for button, candidates in by_button.items():
            gevent = 'press-' + button + '-' + widget.guiId
            self.accept(gevent, self._dispatch_widget_press, [candidates])
            bindings.append(gevent)
        self.widget_bindings[widget] = bindings

    def _dispatch_widget_press(self, candidates, param):
        prefix = param.getModifierButtons().getPrefix()
        for shortcut, event in candidates:
            if prefix + shortcut.rsplit('-', 1)[-1] == shortcut:
                self.messenger.send(event)
                return

    def unbind_widget(self, widget):
        for gevent in self.widget_bindings.pop(widget, []):
            self.ignore(gevent)

    def keystroke_event(self, keyname):
        # TODO: The menu widget should use suppressKey
        if self.gui is not None and self.gui.popup_menu_shown:
            return
        callback_data = self.keystrokes.get(keyname, None)
        if callback_data is not None:
            method, extraArgs = callback_data
            method(*extraArgs)

    def accept(self, event, method, extraArgs=[], direct=False):
        if len(event) == 1 and not direct and not ('A' <= event <= 'z'):
            self.keystrokes[event] = [method, extraArgs]
        else:
            DirectObject.accept(self, event, method, extraArgs=extraArgs)

    def ignore(self, event):
        if len(event) == 1 and event in self.keystrokes:
            del self.keystrokes[event]
        else:
            DirectObject.ignore(self, event)
