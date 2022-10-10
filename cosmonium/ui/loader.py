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


import os
from typing import NamedTuple

from ..parsers.yamlparser import YamlParser
from .menubuilder import EventMenuEntry, SubMenuEntry, MenuSeparator, MenubarEntry, MenubarConfig, MenuConfig


class UIConfig(NamedTuple):
    locale: str
    shortcuts: list
    named_menus: dict
    menubar: list
    popup: list


class UIConfigLoader:

    def __init__(self):
        self.named_menus = {}

    def load(self, ui_config_file):
        parser = YamlParser()
        basedir = os.path.dirname(ui_config_file)
        data = parser.load_and_parse(ui_config_file)
        localedir = data.get('locale', os.path.join(basedir, 'locale'))
        shortcuts_file = data.get('shortcuts')
        if shortcuts_file is not None:
            if not os.path.isabs(shortcuts_file):
                shortcuts_file = os.path.join(basedir, shortcuts_file)
            shortcuts = self.load_shortcuts(shortcuts_file)
        else:
            shortcuts = []
        menubar_file = data.get('menubar')
        if menubar_file is not None:
            if not os.path.isabs(menubar_file):
                menubar_file = os.path.join(basedir, menubar_file)
            menubar = self.load_menubar(menubar_file)
        else:
            menubar = None
        popup_file = data.get('popup')
        if popup_file is not None:
            if not os.path.isabs(popup_file):
                popup_file = os.path.join(basedir, popup_file)
            popup = self.load_popup(popup_file)
        else:
            popup = None
        return UIConfig(locale=localedir,
                        shortcuts=shortcuts,
                        named_menus=self.named_menus,
                        menubar=menubar,
                        popup=popup)

    def load_shortcuts(self, shortcuts_file):
        shortcuts_items = []
        parser = YamlParser()
        data = parser.load_and_parse(shortcuts_file)
        for event, shortcuts in data.items():
            if not isinstance(shortcuts, list):
                shortcuts = [shortcuts]
            shortcuts = [str(shortcut) for shortcut in shortcuts]
            shortcuts_items.append((event, shortcuts))
        return shortcuts_items

    def load_menu_entry(self, data):
        if data is not None:
            text = data.get("title")
            enabled = data.get('enabled')
            if 'event' in data:
                state = data.get('state')
                event = data.get("event")
                menu = EventMenuEntry(text=text, state=state, event=event, enabled=enabled)
            elif 'menu' in data:
                menu = data.get("menu")
                menu = SubMenuEntry(text=text, entries=menu, enabled=enabled)
            else:
                entries = self.load_submenu( data.get("entries", []))
                menu = SubMenuEntry(text=text, entries=entries, enabled=enabled)
        else:
            menu = MenuSeparator()
        return menu

    def load_submenu(self, data):
        submenu = []
        for entry in data:
            entry = self.load_menu_entry(entry)
            submenu.append(entry)
        return submenu

    def load_menubar(self, menubar_file):
        parser = YamlParser()
        data = parser.load_and_parse(menubar_file)
        for name, entries in data.get('menus', {}).items():
            submenu = self.load_submenu(entries)
            self.named_menus[name] = submenu
        entries = []
        for menu_entry in data.get('menubar', []):
            title = menu_entry.get('title')
            submenu = menu_entry.get('entries', [])
            submenu = self.load_submenu(submenu)
            entry = MenubarEntry(title, submenu)
            entries.append(entry)
            menubar = MenubarConfig(entries)
        return menubar

    def load_popup(self, popup_file):
        parser = YamlParser()
        data = parser.load_and_parse(popup_file)
        entries = self.load_submenu(data.get('popup'))
        menuconfig = MenuConfig(entries)
        return menuconfig
