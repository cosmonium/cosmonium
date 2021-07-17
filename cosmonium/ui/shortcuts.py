# -*- coding: utf-8 -*-
#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2021 Laurent Deru.
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

from direct.showbase.DirectObject import DirectObject

import sys

class Shortcuts(DirectObject):
    keymap = {
        'control-q': 'exit',
        'enter': 'gui-search-object',
        'escape': 'escape-dispatch',
        'alt-enter': 'toggle-fullscreen',
        ',': 'zoom-in',
        'shift-,-repeat': 'zoom-in',
        '.': 'zoom-out',
        'shift-.-repeat': 'zoom-out',
        'control-r': 'reset-zoom',
        'control-m': 'gui-toggle-menubar',
        'control-p': 'gui-show-preferences',
        'control-e': 'gui-show-editor',

        'f1': 'gui-show-info',
        'shift-f1': 'gui-show-help',
        'f2': 'debug-connect-pstats',
        'f3': 'debug-toggle-filled-wireframe',
        'shift-f3': 'debug-toggle-wireframe',
        'f4': 'toggle-hdr',
        'f5': 'debug-toggle-buffer-viewer',
        'f7': 'debug-dump-octree-stats',
        'shift-f7': 'debug-dump-octree',
        'f8': 'debug-freeze-lod',
        'shift-f8': 'debug-dump-objects-stats',
        'shift-control-f8': 'debug-dump-objects-info',
        'control-f8': 'debug-toggle-split-merge-log',
        'f9': 'debug-toggle-shader-debug-coord',
        'shift-f9': 'debug-toggle-bounding-boxes',
        'control-f9': 'debug-toggle-lod-frustum',
        'shift-control-f9': 'debug-toggle-shadows-frustum',
        'f10': 'save-screenshot',
        'shift-f10': 'save-screenshot-no-gui',
        'f11': 'debug-scene-ls',
        'shift-f11': 'debug-scene-explore',
        'f12': 'debug-scene-analyze',
        'shift-f12': 'debug-print-tasks',

        'f': 'follow-selected',
        'y': 'sync-selected',
        't': 'track-selected',
        'control-t': 'control-selected',

        'd': 'goto-front',
        'shift-d': 'goto-illuminated-front',
        'g': 'goto-selected',
        'c': 'center-selected',
        'control-j': 'debug-toggle-jump',

        'shift-n': 'goto-north',
        'shift-s': 'goto-south',
        'shift-r': 'goto-meridian',

        'shift-e': 'align-ecliptic',
        'shift-q': 'align-equatorial',

        'control-g': 'goto-surface',

        'h': 'select-home',

        'control-c': 'save-cel-url',
        'control-v': 'load-cel-url',
        'control-o': 'open-script',

        'shift-j': 'set-j2000-date',
        '!': 'set-current-date',
        'l': 'accelerate-time-10',
        'shift-l': 'accelerate-time-2',
        'k': 'slow-time-10',
        'shift-k': 'slow-time-2',
        'j': 'invert-time',
        'space': 'toggle-freeze-time',
        '\\': 'set-real-time',

        '{': 'decrease-ambient',
        '}': 'increase-ambient',

        '[': 'decrease-limit-magnitude',
        ']': 'increase-limit-magnitude',

        #Render
        'control-a': 'toggle-atmosphere',
        'shift-a': 'toggle-rotation-axis',
        'shift-control-r': 'toggle-reference-axis',
        'control-b': 'toggle-constellations-boundaries',
        #'control-e': 'toggle-shadows',
        'i': 'toggle-clouds',
        #'control-l': 'toggle-nightsides',
        'o': 'toggle-orbits',
        #'control-t', toggle-comet-tails',
        'u': 'toggle-body-class-galaxy',
        #'shift-u': 'toggle-globulars',
        ';': 'toggle-equatorial-grid',
        ':': 'toggle-ecliptic-grid',
        '/': 'toggle-asterisms',
        #'^': 'toggle-nebulae',

        #Orbits
        'shift-control-b': 'toggle-orbit-star',
        'shift-control-p': 'toggle-orbit-planet',
        'shift-control-d': 'toggle-orbit-dwarfplanet',
        'shift-control-m': 'toggle-orbit-moon',
        'shift-control-o': 'toggle-orbit-minormoon',
        'shift-control-c': 'toggle-orbit-comet',
        'shift-control-a': 'toggle-orbit-asteroid',
        'shift-control-s': 'toggle-orbit-spacecraft',

        #Labels
        'e': 'toggle-label-galaxy',
        #'shift-e': 'toggle-label-globular',
        'b': 'toggle-label-star',
        'p': 'toggle-label-planet',
        'shift-p': 'toggle-label-dwarfplanet',
        'm': 'toggle-label-moon',
        'shift-m': 'toggle-label-minormoon',
        'shift-w': 'toggle-label-comet',
        'w': 'toggle-label-asteroid',
        'n': 'toggle-label-spacecraft',
        '=': 'toggle-label-constellation',
        #'&': 'toggle-label-location',

        'v': 'toggle-hud',

        '0': "select-object-0",
        '1': "select-object-1",
        '2': "select-object-2",
        '3': "select-object-3",
        '4': "select-object-4",
        '5': "select-object-5",
        '6': "select-object-6",
        '7': "select-object-7",
        '8': "select-object-8",
        '9': "select-object-9",

        'shift-h': 'debug-print-info',
        'shift-y': 'toggle-fly-mode',
    }

    eventmap = None

    def __init__(self, base, messenger, gui):
        DirectObject.__init__(self)
        self.messenger = messenger
        self.gui = gui
        self.keystrokes = {}
        if not base.app_config.test_start:
            base.buttonThrowers[0].node().set_keystroke_event('keystroke')
        self.accept('keystroke', self.keystroke_event)

        if sys.platform == 'darwin':
            modified_keymap = {}
            for (key, event) in self.keymap.items():
                key = key.replace('control', 'meta')
                modified_keymap[key] = event
            Shortcuts.keymap = modified_keymap

        if Shortcuts.eventmap is None:
            Shortcuts.eventmap = {Shortcuts.keymap[key]: key for key in reversed(sorted(Shortcuts.keymap.keys()))}
        for (key, event) in self.keymap.items():
            self.accept(key, self.messenger.send, [event])

    def get_shortcut_for(self, event):
        return self.eventmap.get(event, None)

    def keystroke_event(self, keyname):
        #TODO: The menu widget should use suppressKey
        if self.gui is not None and self.gui.popup_menu_shown: return
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
