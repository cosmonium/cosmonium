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

from collections import defaultdict
from direct.showbase.DirectObject import DirectObject
import sys


class Shortcuts(DirectObject):

    def __init__(self, base, messenger, gui):
        DirectObject.__init__(self)
        self.messenger = messenger
        self.gui = gui
        self.eventmap = defaultdict(lambda: [])
        self.keystrokes = {}
        if not base.app_config.test_start:
            base.buttonThrowers[0].node().set_keystroke_event('keystroke')
        self.accept('keystroke', self.keystroke_event)

    def add(self, event, shortcuts):
        for shortcut in shortcuts:
            if sys.platform == 'darwin':
                shortcut = shortcut.replace('control', 'meta')
                if shortcut == 'f11':
                    shortcut = 'shift-f11'
            self.eventmap[event].append(shortcut)
            self.accept(shortcut, self.messenger.send, [event])

    def set_shortcuts(self, shortcuts_items):
        for event, shortcuts in shortcuts_items:
            self.add(event, shortcuts)

    def get_shortcuts_for(self, event):
        return self.eventmap.get(event, None)

    def keystroke_event(self, keyname):
        # TODO: The menu widget should use suppressKey
        if self.gui is not None and self.gui.popup_menu_shown:
            return
        callback_data = self.keystrokes.get(keyname, None)
        if callback_data is not None:
            (method, extraArgs) = callback_data
            method(*extraArgs)

    def accept(self, event, method, extraArgs=[], direct=False):
        if len(event) == 1 and not direct:
            self.keystrokes[event] = [method, extraArgs]
        else:
            DirectObject.accept(self, event, method, extraArgs=extraArgs)

    def ignore(self, event):
        if len(event) == 1 and event in self.keystrokes:
            del self.keystrokes[event]
        else:
            DirectObject.ignore(self, event)
