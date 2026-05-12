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

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Optional

from ...parsers.yamlloader import YamlLoader
from ..config.models import UIConfigModel
from ..config.validator import ConfigValidator
from .dock import DockLoader
from .hud import HUDLoader
from .menus import MenuLoader
from .shortcuts import ShortcutsLoader
from .skin import SkinLoader

if TYPE_CHECKING:
    from ..gui import Gui


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

    def __init__(self, gui: Gui) -> None:
        """
        Initialize the UI config loader.

        Args:
            global_vars: Dictionary of global variables for expression evaluation
        """
        self.gui = gui

        # Config validator
        self.validator = ConfigValidator()

        # Create specialized loaders
        self.menu_loader = MenuLoader(gui, self.validator)
        self.dock_loader = DockLoader(gui, self.validator)
        self.hud_loader = HUDLoader(gui, self.validator)
        self.skin_loader = SkinLoader(gui, self.validator)
        self.shortcuts_loader = ShortcutsLoader(gui, self.validator)

    def _resolve_path(self, path: Optional[str], basedir: str) -> Optional[str]:
        """
        Resolve a file path relative to the base directory.

        Args:
            path: File path (absolute or relative)
            basedir: Base directory for relative paths

        Returns:
            Absolute path or None if path is None
        """
        if path is None:
            return None
        if os.path.isabs(path):
            return path
        return os.path.join(basedir, path)

    def load(self, ui_config_file: str) -> None:
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
        basedir = os.path.dirname(ui_config_file)
        raw_data = YamlLoader.load_file(ui_config_file, use_splash=False)

        # Validate main config
        data = UIConfigModel.model_validate(raw_data)

        # Load skin first (needed by other components)
        skin_file = self._resolve_path(data.skin, basedir)
        if skin_file is not None:
            skin = self.skin_loader.load(skin_file)
        else:
            skin = None
        self.gui.skin = skin

        # Load locale
        locale = self._resolve_path(data.locale, basedir) or os.path.join(basedir, 'locale')
        self.gui.locale = locale

        # Load shortcuts
        shortcuts_file = self._resolve_path(data.shortcuts, basedir)
        if shortcuts_file is not None:
            self.gui.shortcuts_config = self.shortcuts_loader.load(shortcuts_file)
        else:
            self.gui.shortcuts_config = []

        # Load menubar
        menubar_file = self._resolve_path(data.menubar, basedir)
        if menubar_file is not None:
            named_menus, menubar_config = self.menu_loader.load_menubar(menubar_file)
            self.gui.named_menus = named_menus
            self.gui.menubar_config = menubar_config
        else:
            self.gui.menubar_config = None

        # Load popup menu
        popup_file = self._resolve_path(data.popup, basedir)
        if popup_file is not None:
            self.gui.popup_config = self.menu_loader.load_popup(popup_file)
        else:
            self.gui.popup_config = None

        # Load dock
        dock_file = self._resolve_path(data.dock, basedir)
        if dock_file is not None:
            self.gui.dock_config = self.dock_loader.load(dock_file)
        else:
            self.gui.dock_config = None

        # Load HUD
        hud_file = self._resolve_path(data.hud, basedir)
        if hud_file is not None:
            self.gui.hud_config = self.hud_loader.load(hud_file)
        else:
            self.gui.hud_config = {}
