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


"""
Menu loader.

This module handles loading of menu and menubar configurations from YAML files.
"""

from ...parsers.yamlparser import YamlParser
from ..menubuilder import EventMenuEntry, SubMenuEntry, MenuSeparator, MenubarEntry, MenubarConfig, MenuConfig
from ..templates.expression import PythonExpressionParser, true_expression, zero_expression
from .base import BaseComponentLoader


class MenuLoader(BaseComponentLoader):
    """
    Loader for menu and menubar configurations.

    Handles loading of menu structures including menu entries, submenus,
    separators, and menu bars with dynamic state expressions.
    """

    def __init__(self, global_vars):
        """
        Initialize the menu loader with global variables for expressions.

        Args:
            global_vars: Dictionary of global variables for expression evaluation
        """
        self.global_vars = global_vars
        self.expression_parser = PythonExpressionParser()
        self.named_menus = {}

    def load_menu_entry(self, data):
        """
        Load a single menu entry from configuration data.

        Args:
            data: Dictionary containing menu entry configuration

        Returns:
            MenuEntry instance (EventMenuEntry, SubMenuEntry, or MenuSeparator)
        """
        if data is not None:
            text = data.get("title")

            # Parse enabled condition
            enabled_source = data.get('enabled')
            if enabled_source is not None:
                enabled = self.expression_parser.compile_expression(enabled_source, self.global_vars)
            else:
                enabled = true_expression

            # Parse visible condition
            visible_source = data.get('visible')
            if visible_source is not None:
                visible = self.expression_parser.compile_expression(visible_source, self.global_vars)
            else:
                visible = true_expression

            if 'event' in data:
                # Event menu entry
                state_source = data.get('state')
                if state_source is not None:
                    state = self.expression_parser.compile_expression(state_source, self.global_vars)
                else:
                    state = zero_expression
                event = data.get("event")
                menu = EventMenuEntry(text=text, state=state, event=event, enabled=enabled, visible=visible)
            elif 'menu' in data:
                # Named submenu reference
                menu = data.get("menu")
                menu = SubMenuEntry(text=text, entries=menu, enabled=enabled, visible=visible)
            elif 'title' in data:
                # Inline submenu
                entries = self.load_submenu(data.get("entries", []))
                menu = SubMenuEntry(text=text, entries=entries, enabled=enabled, visible=visible)
            else:
                # Separator
                menu = MenuSeparator(visible=visible)
        else:
            menu = MenuSeparator(visible=true_expression)

        return menu

    def load_submenu(self, data):
        """
        Load a submenu (list of menu entries) from configuration data.

        Args:
            data: List of menu entry configurations

        Returns:
            List of MenuEntry instances
        """
        submenu = []
        for entry in data:
            entry = self.load_menu_entry(entry)
            submenu.append(entry)
        return submenu

    def load_menubar(self, filepath):
        """
        Load a menubar configuration from a YAML file.

        Args:
            filepath: Path to menubar YAML file
            global_vars: Dictionary of global variables for expression evaluation

        Returns:
            MenubarConfig instance
        """
        parser = YamlParser()
        data = parser.load_and_parse(filepath)

        # Load named menus that can be referenced elsewhere
        for name, entries in data.get('menus', {}).items():
            submenu = self.load_submenu(entries)
            self.named_menus[name] = submenu

        # Load menubar entries
        entries = []
        for menu_entry in data.get('menubar', []):
            title = menu_entry.get('title')
            submenu = menu_entry.get('entries', [])
            submenu = self.load_submenu(submenu)
            entry = MenubarEntry(title, submenu)
            entries.append(entry)

        menubar = MenubarConfig(entries)
        return menubar

    def load_popup(self, filepath):
        """
        Load a popup menu configuration from a YAML file.

        Args:
            filepath: Path to popup YAML file
            global_vars: Dictionary of global variables for expression evaluation

        Returns:
            MenuConfig instance
        """
        parser = YamlParser()
        data = parser.load_and_parse(filepath)
        entries = self.load_submenu(data.get('popup'))
        menuconfig = MenuConfig(entries)
        return menuconfig

    def load(self, filepath):
        """
        Load a menu configuration from a file.

        This method delegates to either load_menubar or load_popup
        based on the file content structure.

        Args:
            filepath: Path to menu configuration file
            global_vars: Dictionary of global variables for expression evaluation

        Returns:
            MenubarConfig or MenuConfig instance
        """
        # No type detection yet, default to menubar
        return self.load_menubar(filepath)
