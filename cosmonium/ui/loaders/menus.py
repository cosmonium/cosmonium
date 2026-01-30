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
from ..config.models import MenubarConfigModel, MenuEntryConfig, PopupMenuConfig
from ..menus.menubuilder import EventMenuEntry, MenubarConfig, MenubarEntry, MenuConfig, MenuSeparator, SubMenuEntry
from ..templates.expression import PythonExpressionParser, true_expression, zero_expression
from .base import BaseComponentLoader


class MenuLoader(BaseComponentLoader):
    """
    Loader for menu and menubar configurations.

    Handles loading of menu structures including menu entries, submenus,
    separators, and menu bars with dynamic state expressions.
    """

    def __init__(self, gui, validator):
        """
        Initialize the menu loader with global variables for expressions.

        Args:
            gui: UI instance
            validator: ConfigValidator instance
        """
        self.gui = gui
        self.validator = validator
        self.expression_parser = PythonExpressionParser()

    def load_menu_entry(self, entry_config: MenuEntryConfig):
        """
        Load a single menu entry from configuration data.

        Args:
            entry_config: MenuEntryConfig Pydantic model or None for separator

        Returns:
            MenuEntry instance (EventMenuEntry, SubMenuEntry, or MenuSeparator)
        """
        if entry_config is None:
            return MenuSeparator(visible=true_expression)

        # Parse enabled condition
        if entry_config.enabled is not None:
            enabled = self.expression_parser.compile_expression(entry_config.enabled, self.gui.global_vars.globals)
        else:
            enabled = true_expression

        # Parse visible condition
        if entry_config.visible is not None:
            visible = self.expression_parser.compile_expression(entry_config.visible, self.gui.global_vars.globals)
        else:
            visible = true_expression

        if entry_config.event is not None:
            # Event menu entry
            if entry_config.state is not None:
                state = self.expression_parser.compile_expression(entry_config.state, self.gui.global_vars.globals)
            else:
                state = zero_expression
            menu = EventMenuEntry(
                text=entry_config.title, state=state, event=entry_config.event, enabled=enabled, visible=visible
            )
        elif entry_config.menu is not None:
            # Named submenu reference
            menu = SubMenuEntry(text=entry_config.title, entries=entry_config.menu, enabled=enabled, visible=visible)
        elif entry_config.title is not None:
            # Inline submenu
            entries = self.load_submenu(entry_config.entries if entry_config.entries else [])
            menu = SubMenuEntry(text=entry_config.title, entries=entries, enabled=enabled, visible=visible)
        else:
            # Separator
            menu = MenuSeparator(visible=visible)

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

        Returns:
            Tuple with named menus dict and MenubarConfig instance
        """
        parser = YamlParser()
        data = parser.load_and_parse(filepath)

        # Validate menubar configuration
        validated = self.validator.validate_dict(data, MenubarConfigModel)

        # Load named menus that can be referenced elsewhere
        named_menus = {}
        for name, entries in validated.menus.items():
            submenu = self.load_submenu(entries)
            named_menus[name] = submenu

        # Load menubar entries
        entries = []
        for menu_entry in validated.menubar:
            # menu_entry is MenubarEntryConfig Pydantic model
            submenu = self.load_submenu(menu_entry.entries)
            entry = MenubarEntry(menu_entry.title, submenu)
            entries.append(entry)

        menubar = MenubarConfig(entries)
        return named_menus, menubar

    def load_popup(self, filepath):
        """
        Load a popup menu configuration from a YAML file.

        Args:
            filepath: Path to popup YAML file

        Returns:
            MenuConfig instance
        """
        parser = YamlParser()
        data = parser.load_and_parse(filepath)

        # Validate popup configuration
        validated = self.validator.validate_dict(data, PopupMenuConfig)
        entries = self.load_submenu(validated.popup)

        menuconfig = MenuConfig(entries)
        return menuconfig

    def load(self, filepath):
        """
        Load a menu configuration from a file.

        This method delegates to either load_menubar or load_popup
        based on the file content structure.

        Args:
            filepath: Path to menu configuration file

        Returns:
            MenubarConfig or MenuConfig instance
        """
        # No type detection yet, default to menubar
        return self.load_menubar(filepath)
