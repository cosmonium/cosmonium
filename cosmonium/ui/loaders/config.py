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

from ...parsers.yamlparser import YamlParser

from .menus import MenuLoader
from .dock import DockLoader
from .hud import HUDLoader
from .skin import SkinLoader
from .shortcuts import ShortcutsLoader


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

    def __init__(self, gui):
        """
        Initialize the UI config loader.

        Args:
            global_vars: Dictionary of global variables for expression evaluation
        """
        self.gui = gui

        # Initialize specialized loaders
        self.menu_loader = MenuLoader(gui)
        self.dock_loader = DockLoader(gui)
        self.hud_loader = HUDLoader(gui)
        self.skin_loader = SkinLoader(gui)
        self.shortcuts_loader = ShortcutsLoader(gui)

        # For backward compatibility - expose named_menus
        self.named_menus = self.menu_loader.named_menus

    def load(self, ui_config_file):
        """
        Load complete UI configuration from a main config file and apply directly to GUI.

        This method loads all UI components and applies them directly to the
        GUI instance instead of returning an intermediate configuration object.

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
        """
        parser = YamlParser()
        basedir = os.path.dirname(ui_config_file)
        data = parser.load_and_parse(ui_config_file)

        # Load skin first (needed by other components)
        skin_file = data.get('skin')
        if skin_file is not None:
            if not os.path.isabs(skin_file):
                skin_file = os.path.join(basedir, skin_file)
            skin = self.load_skin_file(skin_file)
        else:
            skin = None
        self.gui.skin = skin

        # Apply locale directly
        locale = data.get('locale', os.path.join(basedir, 'locale'))
        self.gui.locale = locale

        # Apply shortcuts directly
        shortcuts_file = data.get('shortcuts')
        if shortcuts_file is not None:
            if not os.path.isabs(shortcuts_file):
                shortcuts_file = os.path.join(basedir, shortcuts_file)
            self.gui.shortcuts_config = self.load_shortcuts(shortcuts_file)
        else:
            self.gui.shortcuts_config = []

        # Apply menubar directly
        menubar_file = data.get('menubar')
        if menubar_file is not None:
            if not os.path.isabs(menubar_file):
                menubar_file = os.path.join(basedir, menubar_file)
            self.gui.menubar_config = self.load_menubar(menubar_file)
        else:
            self.gui.menubar_config = None

        # Apply popup directly
        popup_file = data.get('popup')
        if popup_file is not None:
            if not os.path.isabs(popup_file):
                popup_file = os.path.join(basedir, popup_file)
            self.gui.popup_config = self.load_popup(popup_file)
        else:
            self.gui.popup_config = None

        # Apply dock directly
        dock_file = data.get('dock')
        if dock_file is not None:
            if not os.path.isabs(dock_file):
                dock_file = os.path.join(basedir, dock_file)
            self.gui.dock_config = self.load_dock_file(dock_file)
        else:
            self.gui.dock_config = None

        # Apply HUD directly
        hud_file = data.get('hud')
        if hud_file is not None:
            if not os.path.isabs(hud_file):
                hud_file = os.path.join(basedir, hud_file)
            self.gui.hud_config = self.load_hud_file(hud_file)
        else:
            self.gui.hud_config = {}

        # Store named_menus for backward compatibility
        self.gui.named_menus = self.named_menus

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
