#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2022 Laurent Deru.
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

from functools import partial
from typing import NamedTuple

from .menucommon import create_orbiting_bodies_menu, create_orbits_menu, create_surfaces_menu, create_extra_info_menu
from .menucommon import create_select_camera_controller_menu, create_select_ship_menu


class MenubarConfig(NamedTuple):
    entries:list


class MenuConfig(NamedTuple):
    entries:list


class MenubarEntry(NamedTuple):
    text:str
    entries:list


class MenuSeparator(NamedTuple):
    pass


class EventMenuEntry(NamedTuple):
    text:str
    state:str
    enabled:str
    event:str


class SubMenuEntry(NamedTuple):
    text:str
    enabled:str
    entries:list


class MenuBuilder:
    def __init__(self, messenger, shortcuts, states_provider, engine, mouse, browser):
        self.messenger = messenger
        self.shortcuts = shortcuts
        self.states_provider = states_provider
        self.engine = engine
        self.mouse = mouse
        self.browser = browser
        self.items = []
        self.menu_generators = {
            'orbiting-bodies': lambda: create_orbiting_bodies_menu(self.engine, self.engine.selected),
            'over-orbiting-bodies': lambda: create_orbiting_bodies_menu(self.engine, self.mouse.over),
            'orbits': lambda: create_orbits_menu(self.engine, self.engine.selected),
            'over-orbits': lambda: create_orbits_menu(self.engine, self.mouse.over),
            'extra-info': lambda: create_extra_info_menu(self.browser, self.engine.selected),
            'over-extra-info': lambda: create_extra_info_menu(self.browser, self.mouse.over),
            'surfaces': lambda: create_surfaces_menu(self.engine.selected),
            'over-surfaces': lambda: create_surfaces_menu(self.mouse.over),
            'over-extra-info': lambda: create_extra_info_menu(self.browser, self.mouse.over),
            'select-camera-controller': lambda: create_select_camera_controller_menu(self.engine),
            'select-ship': lambda: create_select_ship_menu(self.engine),
            }
        self.text_generators = {
            'over-name': lambda: (self.mouse.over.get_friendly_name() if self.mouse.over is not None else '')
            }

    def add_named_menu(self, name, entries):
        self.menu_generators[name] = lambda: self.create_submenu(entries)

    def get_auto_menu(self, menu_name):
        generator = self.menu_generators.get(menu_name)
        if generator:
            entries = generator()
        else:
            print(f"Menu {menu_name} not found")
            entries = []
        return entries

    def get_auto_text(self, text):
        generator = self.text_generators.get(text)
        if generator:
            text = generator()
        else:
            print(f"Text {text} not found")
        return text

    def menu_event(self, text, state, event, condition=None, args=[]):
        if text[0] == '@':
            text = self.get_auto_text(text[1:])
        shortcut = None #self.shortcuts.get_shortcut_for(event)
        if shortcut is not None:
            full_text = text + '>' + shortcut.title()
        else:
            full_text = text
        action = self.messenger.send
        if event == 0 or (condition is not None and not condition):
            action = 0
        return (full_text, state, action, event, args)

    def menu_submenu(self, text, submenu, condition=None):
        if condition is None or condition:
            if isinstance(submenu, str):
                entries = self.get_auto_menu(submenu)
            else:
                entries = self.create_submenu(submenu)
        else:
            entries = []
        return (text, 0, entries)

    def create_menu_entry(self, entry):
        if entry.enabled is not None:
            enabled = self.states_provider.get_state(entry.enabled)
        else:
            enabled = None
        if isinstance(entry, EventMenuEntry):
            if entry.state is not None:
                state = self.states_provider.get_state(entry.state)
            else:
                state = 0
            return self.menu_event(_(entry.text), state, entry.event, condition=enabled)
        else:
            return self.menu_submenu(_(entry.text), entry.entries, condition=enabled)

    def create_submenu(self, entries):
        submenu = []
        for entry in entries:
            if not isinstance(entry, MenuSeparator):
                submenu.append(self.create_menu_entry(entry))
            else:
                submenu.append(0)
        return submenu

    def create_menu(self, menu_config):
        return partial(self.create_submenu, menu_config.entries)

    def create_menubar(self, menubar_config):
        menu = []
        for item in menubar_config.entries:
            menu.append((_(item.text), partial(self.create_submenu, item.entries)))
        return menu
