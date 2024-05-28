#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2023 Laurent Deru.
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
from .skin import ParentSelector, Selector, UISkinEntry, UISkin
from .menubuilder import EventMenuEntry, SubMenuEntry, MenuSeparator, MenubarEntry, MenubarConfig, MenuConfig
from .dock.button import ButtonDockWidget
from .dock.layouts import LayoutDockWidget, SpaceDockWidget
from .dock.text import TextDockWidget
from panda3d.core import LColor, TextNode, LVector4


class UIConfig(NamedTuple):
    locale: str
    shortcuts: list
    named_menus: dict
    menubar: list
    popup: list
    dock: list
    skin: UISkin


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
        dock_file = data.get('dock')
        if dock_file is not None:
            if not os.path.isabs(dock_file):
                dock_file = os.path.join(basedir, dock_file)
            dock = self.load_dock_file(dock_file)
        else:
            dock = None
        skin_file = data.get('skin')
        if skin_file is not None:
            if not os.path.isabs(skin_file):
                skin_file = os.path.join(basedir, skin_file)
            skin = self.load_skin_file(skin_file)
        else:
            skin = None
        return UIConfig(locale=localedir,
                        shortcuts=shortcuts,
                        named_menus=self.named_menus,
                        menubar=menubar,
                        popup=popup,
                        dock=dock,
                        skin=skin)

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
            visible = data.get('visible')
            if 'event' in data:
                state = data.get('state')
                event = data.get("event")
                menu = EventMenuEntry(text=text, state=state, event=event, enabled=enabled, visible=visible)
            elif 'menu' in data:
                menu = data.get("menu")
                menu = SubMenuEntry(text=text, entries=menu, enabled=enabled, visible=visible)
            elif 'title' in data:
                entries = self.load_submenu( data.get("entries", []))
                menu = SubMenuEntry(text=text, entries=entries, enabled=enabled, visible=visible)
            else:
                menu = MenuSeparator(visible=visible)
        else:
            menu = MenuSeparator(visible=None)
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

    def parse_alignments(self, value, default=('min', 'min')):
        if isinstance(value, list) and len(value) == 2:
            if value[0] == "left":
                value[0] = "min"
            elif value[0] == "right":
                value[0] = "max"
            if value[1] == "top":
                value[1] = "min"
            elif value[1] == "bottom":
                value[1] = "max"
            return value
        elif value is None:
            return default
        else:
            print(f"Invalid alignments {value}")
            return default

    def parse_borders(self, value):
        if isinstance(value, list) and len(value) == 4:
            return LVector4(*value)
        elif isinstance(value, int):
            return LVector4(value)
        elif value is None:
            return None
        else:
            print(f"Invalid borders {value}")
            return None

    def parse_gaps(self, value, default=(0, 0)):
        if isinstance(value, list) and len(value) == 2:
            return value
        elif isinstance(value, int):
            return (value, value)
        elif value is None:
            return default
        else:
            print(f"Invalid gaps {value}")
            return default

    def parse_text_align(self, value, default=TextNode.A_boxed_left):
        if value == "left":
            return TextNode.A_boxed_left
        elif value == "center":
            return TextNode.A_boxed_center
        elif value == "right":
            return TextNode.A_boxed_right
        elif value is None:
            return default
        else:
            print(f"Invalid text align {value}")
            return default

    def load_widget_button(self, data):
        alignments = self.parse_alignments(data.get('align'))
        borders = self.parse_borders(data.get('borders'))
        if 'text' in data:
            text = data.get('text')
            rescale = False
        elif 'code' in data:
            code = int(data['code'], 16)
            text = chr(code)
            rescale = data.get('rescale', True)
        else:
            text = None
        event = data.get('event')
        size = data.get('size', None)
        button = ButtonDockWidget(text, event, size, rescale=rescale, alignments=alignments, borders=borders)
        return button

    def load_widget_text(self, data):
        alignments = self.parse_alignments(data.get('align'))
        borders = self.parse_borders(data.get('borders'))
        text = data.get('text')
        data_id = data.get('data')
        size = data.get('size', None)
        align = self.parse_text_align(data.get('align'))
        text = TextDockWidget(text, data_id, size=size, align=align, alignments=alignments, borders=borders)
        return text

    def load_widget_spacer(self, data):
        alignments = self.parse_alignments(data.get('align'), ("min", "min"))
        size = tuple(data.get('size', (0, 0)))
        spacer = SpaceDockWidget(size=size, alignments=alignments, borders=None)
        return spacer

    def load_widget_layout(self, data):
        alignments = self.parse_alignments(data.get('align'))
        borders = self.parse_borders(data.get('borders'))
        gaps = self.parse_gaps(data.get('gaps'))
        size = data.get('size', 32)
        decoration_size = data.get('decoration-size', (1, 1))
        orientation = data.get('orientation', 'horizontal')
        widgets = []
        for widget_data in data.get('widgets', []):
            widget = self.load_widget(widget_data)
            if widget is not None:
                widgets.append(widget)
        return LayoutDockWidget(
            size, orientation, widgets,
            decoration_size=decoration_size,
            alignments=alignments, borders=borders,
            gaps=gaps)

    def load_widget(self, data):
        type = data.get('type')
        if type == 'button':
            return self.load_widget_button(data)
        elif type == "layout":
            return self.load_widget_layout(data)
        elif type == 'spacer':
            return self.load_widget_spacer(data)
        elif type == 'text':
            return self.load_widget_text(data)
        else:
            print(f"Unsupported type {type}")
            return None

    def load_dock(self, data):
        orientation = data.get('orientation', 'horizontal')
        location = data.get('location', 'bottom')
        layout = self.load_widget_layout(data)
        return layout, orientation, location

    def load_dock_file(self, dock_file):
        parser = YamlParser()
        data = parser.load_and_parse(dock_file)
        dock = self.load_dock(data.get('dock'))
        return dock

    @staticmethod
    def parse_color(data):
        if data is not None:
            if isinstance(data, str):
                if len(data) == 7 and data.startswith('#'):
                    color = LColor(*tuple(int(data[i:i + 2], 16) / 255 for i in (1, 3, 5)), 1.0)
                else:
                    print(f"Invalid color {data}")
                    color = None
            elif isinstance(data, list):
                if len(data) == 4:
                    color = LColor(*data)
                elif len(data) == 3:
                    color = LColor(*data, 1.0)
                else:
                    print(f"Invalid color {data}")
                    color = None
        else:
            color = None
        return color

    @staticmethod
    def parse_length(data, entry):
        if data is not None:
            if isinstance(data, str):
                if len(data) >= 3:
                    value = float(data[0:-2])
                    unit = data[-2:]
                if unit == 'px':
                    size = lambda element, font_size, skin: entry.calc_size_px(value, element, font_size, skin)
                elif unit == 'em':
                    size = lambda element, font_size, skin: entry.calc_size_em(value, element, font_size, skin)
                else:
                    print(f"Invalid size {data}")
                    size = None
            elif isinstance(data, (int, float)):
                size = lambda element, font_size, skin: entry.calc_size_px(data, element, font_size, skin)
            else:
                print(f"Invalid size {data}")
                size = None
        else:
            size = None
        return size

    @classmethod
    def parse_edge_lengths(cls, data, entry):
        if data is None:
            return None
        if isinstance(data, str):
            items = data.split(' ')
        lengths = [cls.parse_length(item, entry) for item in items]
        # DirectGUI order is : l, r, b, t
        if len(lengths) == 1:
            lengths = lengths * 4
        elif len(lengths) == 2:
            lengths = [lengths[1], lengths[1], lengths[0], lengths[0]]
        elif len(lengths) == 3:
            lengths = [lengths[1], lengths[1], lengths[2], lengths[0]]
        else:
            lengths = [lengths[3], lengths[1], lengths[2], lengths[0]]
        return lengths

    def load_skin_selector(self, data):
        element = data.get('element', None)
        state = data.get('state', None)
        class_ = data.get('class', None)
        id_ = data.get('id', None)
        selector = Selector(element, state, class_, id_)
        if 'parent' in data:
            parent_selector = self.load_skin_selector(data['parent'])
            selector = ParentSelector(parent_selector, selector)
        return selector

    def load_skin_entry(self, data):
        selector = self.load_skin_selector(data)
        entry = UISkinEntry(selector, {})
        entry.background_color = self.parse_color(data.get('background-color'))
        entry.text_color = self.parse_color(data.get('text-color'))
        entry.border_color = self.parse_color(data.get('border-color'))
        entry.font_family = data.get('font-family')
        entry.font_size = self.parse_length(data.get('font-size'), entry)
        entry.font_style = data.get('font-style')
        entry.font_weight = data.get('font-weight')
        entry.margin = self.parse_edge_lengths(data.get('margin'), entry)
        entry.padding = self.parse_edge_lengths(data.get('padding'), entry)
        entry.width = self.parse_length(data.get('width'), entry)
        entry.height = self.parse_length(data.get('height'), entry)
        return entry

    def load_skin(self, data):
        skin = UISkin()
        for entry_data in data:
            entry = self.load_skin_entry(entry_data)
            skin.add_entry(entry)
        return skin

    def load_skin_file(self, skin_file):
        parser = YamlParser()
        data = parser.load_and_parse(skin_file)
        skin = self.load_skin(data)
        return skin
