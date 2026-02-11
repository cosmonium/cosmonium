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
Shortcuts loader.

This module handles loading of keyboard shortcuts from configuration files.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple

from ...parsers.yamlparser import YamlParser
from .base import BaseComponentLoader

if TYPE_CHECKING:
    from ..config.validator import ConfigValidator
    from ..gui import Gui


class ShortcutsLoader(BaseComponentLoader):
    """
    Loader for keyboard shortcuts configuration.

    Loads shortcut bindings from YAML files mapping events to key combinations.
    """

    def __init__(self, gui: Gui, validator: ConfigValidator) -> None:
        """Initialize the skin loader with parsers.

        Args:
            gui: UI instance
            validator: ConfigValidator instance
        """
        self.gui = gui
        self.validator = validator

    def load(self, filepath: str) -> List[Tuple[str, List[str]]]:
        """
        Load shortcuts from a configuration file.

        Args:
            filepath: Path to shortcuts YAML file

        Returns:
            List of (event, shortcuts) tuples
        """
        shortcuts_items = []
        parser = YamlParser()
        data = parser.load_and_parse(filepath, use_splash=False)

        for event, shortcuts in data.items():
            if not isinstance(shortcuts, list):
                shortcuts = [shortcuts]
            shortcuts = [str(shortcut) for shortcut in shortcuts]
            shortcuts_items.append((event, shortcuts))

        return shortcuts_items
