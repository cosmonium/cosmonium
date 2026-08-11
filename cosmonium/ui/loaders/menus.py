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

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from ...parsers.yamlloader import YamlLoader
from ..config.models import MenuEntryConfig, MenusConfigModel, PopupMenuConfig
from ..menus.menubuilder import EventMenuEntry, MenubarConfig, MenuConfig, MenuSeparator, SubMenuEntry
from ..templates.expression import PythonExpressionParser, true_expression, zero_expression
from .base import BaseComponentLoader

if TYPE_CHECKING:
    from ..config.validator import ConfigValidator
    from ..gui import Gui


class MenuLoader(BaseComponentLoader):
    """
    Loader for menu and menubar configurations.

    Handles loading of menu structures including menu entries, submenus,
    separators, and menu bars with dynamic state expressions.
    """

    def __init__(self, gui: Gui, validator: ConfigValidator) -> None:
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

    def load_submenu(self, data: List[Any]) -> List[Any]:
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

    def load_named_menus(self, menus_data: Dict[str, List[Any]]) -> Dict[str, List[Any]]:
        """
        Load a 'menus' mapping (named, reusable submenus) from configuration data.

        Args:
            menus_data: Dict of menu name -> list of menu entry configurations

        Returns:
            Dict of menu name -> list of loaded MenuEntry instances
        """
        named_menus = {}
        for name, entries in menus_data.items():
            named_menus[name] = self.load_submenu(entries)
        return named_menus

    def load_menus(self, filepath: str) -> Tuple[Dict[str, List[Any]], MenubarConfig]:
        """
        Load a menus configuration from a YAML file.

        Args:
            filepath: Path to menus YAML file

        Returns:
            Tuple with named menus dict and optional MenubarConfig instance
        """
        data = YamlLoader.load_file(filepath, use_splash=False)

        # Validate menus configuration
        validated = self.validator.validate_dict(data, MenusConfigModel)

        # Load named menus that can be referenced elsewhere
        named_menus = self.load_named_menus(validated.menus)

        # Load menubar if specified
        if validated.menubar is not None:
            entries = self.load_submenu(validated.menubar)
            menubar = MenubarConfig(entries)
        else:
            menubar = None

        return named_menus, menubar

    def load_popup(self, filepath: str) -> MenuConfig:
        """
        Load a popup menu configuration from a YAML file.

        Args:
            filepath: Path to popup YAML file

        Returns:
            MenuConfig instance
        """
        data = YamlLoader.load_file(filepath, use_splash=False)

        # Validate popup configuration
        validated = self.validator.validate_dict(data, PopupMenuConfig)
        entries = self.load_submenu(validated.popup)

        menuconfig = MenuConfig(entries)
        return menuconfig

    def load(self, filepath: str) -> Any:
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
