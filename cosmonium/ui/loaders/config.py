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
Main UI configuration loader.
"""

import os
from typing import NamedTuple

from ...parsers.yamlparser import YamlParser
from ..skin import UISkin

from .menus import MenuLoader
from .dock import DockLoader
from .hud import HUDLoader
from .skin import SkinLoader
from .shortcuts import ShortcutsLoader


class UIConfig(NamedTuple):
    """
    Container for all UI configuration data.

    Attributes:
        locale: Path to locale directory for translations
        shortcuts: List of (event, shortcuts) tuples for keyboard bindings
        named_menus: Dictionary of named menu configurations
        menubar: MenubarConfig instance for the main menu bar
        popup: MenuConfig instance for context menu
        dock: Tuple of (layout, orientation, location) for dock widget
        hud: Dictionary mapping anchor positions to HUD widgets
        skin: UISkin instance for UI styling
    """

    locale: str
    shortcuts: list
    named_menus: dict
    menubar: object
    popup: object
    dock: object
    hud: dict
    skin: UISkin


class UIConfigLoader:
    """
    Main UI configuration loader.

    This class orchestrates the loading of all UI components from configuration
    files. It maintains backward compatibility with the original loader API while
    using specialized loaders internally.

    The loader is initialized with global variables used for expression evaluation
    in menu conditions, HUD visibility, etc.

    Attributes:
        global_vars: Dictionary of global variables for expressions
        parsers: ParsersCollection for parsing common values
        widget_registry: WidgetLoaderRegistry for widget loading
        menu_loader: MenuLoader for menu/menubar loading
        dock_loader: DockLoader for dock loading
        hud_loader: HUDLoader for HUD loading
        skin_loader: SkinLoader for skin loading
        shortcuts_loader: ShortcutsLoader for shortcuts loading
    """

    def __init__(self, gui, global_vars):
        """
        Initialize the UI config loader.

        Args:
            global_vars: Dictionary of global variables for expression evaluation
        """
        self.gui = gui
        self.global_vars = global_vars

        # Initialize specialized loaders
        self.menu_loader = MenuLoader(global_vars)
        self.dock_loader = DockLoader(gui, global_vars)
        self.hud_loader = HUDLoader(global_vars)
        self.skin_loader = SkinLoader()
        self.shortcuts_loader = ShortcutsLoader()

        # For backward compatibility - expose named_menus
        self.named_menus = self.menu_loader.named_menus

    def load(self, ui_config_file):
        """
        Load complete UI configuration from a main config file.

        The main config file should contain paths to component-specific files:
        - shortcuts: path to shortcuts.yaml
        - menubar: path to menubar.yaml
        - popup: path to popup.yaml
        - dock: path to dock.yaml
        - hud: path to hud.yaml
        - skin: path to skin.yaml
        - locale: path to locale directory (optional)

        Args:
            ui_config_file: Path to main UI configuration file

        Returns:
            UIConfig instance containing all loaded components
        """
        parser = YamlParser()
        basedir = os.path.dirname(ui_config_file)
        data = parser.load_and_parse(ui_config_file)

        # Load locale directory
        localedir = data.get('locale', os.path.join(basedir, 'locale'))

        # Load skin
        skin_file = data.get('skin')
        if skin_file is not None:
            if not os.path.isabs(skin_file):
                skin_file = os.path.join(basedir, skin_file)
            skin = self.load_skin_file(skin_file)
        else:
            skin = None
        # TODO: Skin must be available in gui module for the loaders below
        self.gui.skin = skin

        # Load shortcuts
        shortcuts_file = data.get('shortcuts')
        if shortcuts_file is not None:
            if not os.path.isabs(shortcuts_file):
                shortcuts_file = os.path.join(basedir, shortcuts_file)
            shortcuts = self.load_shortcuts(shortcuts_file)
        else:
            shortcuts = []

        # Load menubar
        menubar_file = data.get('menubar')
        if menubar_file is not None:
            if not os.path.isabs(menubar_file):
                menubar_file = os.path.join(basedir, menubar_file)
            menubar = self.load_menubar(menubar_file)
        else:
            menubar = None

        # Load popup menu
        popup_file = data.get('popup')
        if popup_file is not None:
            if not os.path.isabs(popup_file):
                popup_file = os.path.join(basedir, popup_file)
            popup = self.load_popup(popup_file)
        else:
            popup = None

        # Load dock
        dock_file = data.get('dock')
        if dock_file is not None:
            if not os.path.isabs(dock_file):
                dock_file = os.path.join(basedir, dock_file)
            dock = self.load_dock_file(dock_file)
        else:
            dock = None

        # Load HUD
        hud_file = data.get('hud')
        if hud_file is not None:
            if not os.path.isabs(hud_file):
                hud_file = os.path.join(basedir, hud_file)
            hud = self.load_hud_file(hud_file)
        else:
            hud = {}

        return UIConfig(
            locale=localedir,
            shortcuts=shortcuts,
            named_menus=self.named_menus,
            menubar=menubar,
            popup=popup,
            dock=dock,
            hud=hud,
            skin=skin,
        )

    def load_shortcuts(self, shortcuts_file):
        """
        Load keyboard shortcuts from a file.

        Args:
            shortcuts_file: Path to shortcuts configuration file

        Returns:
            List of (event, shortcuts) tuples
        """
        return self.shortcuts_loader.load(shortcuts_file)

    def load_menubar(self, menubar_file):
        """
        Load menubar configuration from a file.

        Args:
            menubar_file: Path to menubar configuration file

        Returns:
            MenubarConfig instance
        """
        return self.menu_loader.load_menubar(menubar_file)

    def load_popup(self, popup_file):
        """
        Load popup menu configuration from a file.

        Args:
            popup_file: Path to popup menu configuration file

        Returns:
            MenuConfig instance
        """
        return self.menu_loader.load_popup(popup_file)

    def load_dock_file(self, dock_file):
        """
        Load dock configuration from a file.

        Args:
            dock_file: Path to dock configuration file

        Returns:
            Tuple of (layout, orientation, location)
        """
        return self.dock_loader.load(dock_file)

    def load_hud_file(self, hud_file):
        """
        Load HUD configuration from a file.

        Args:
            hud_file: Path to HUD configuration file

        Returns:
            Dictionary mapping anchor names to lists of HUD widgets
        """
        return self.hud_loader.load(hud_file)

    def load_skin_file(self, skin_file):
        """
        Load skin configuration from a file.

        Args:
            skin_file: Path to skin configuration file

        Returns:
            UISkin instance
        """
        return self.skin_loader.load(skin_file)
