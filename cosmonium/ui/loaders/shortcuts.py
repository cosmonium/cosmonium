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

from typing import TYPE_CHECKING, List

from pydantic import TypeAdapter, ValidationError

from ...parsers.validator import ConfigValidationError
from ...parsers.yamlloader import YamlLoader
from ..config.models import ShortcutCategoryConfig
from .base import BaseComponentLoader

if TYPE_CHECKING:
    from ...parsers.validator import ConfigValidator
    from ..gui import Gui


# A shortcuts file is a top-level list of user-defined categories, so it is validated with a
# TypeAdapter rather than ConfigValidator.validate_dict.
_SHORTCUTS_FILE_ADAPTER = TypeAdapter(List[ShortcutCategoryConfig])


class ShortcutsLoader(BaseComponentLoader):
    """
    Loader for keyboard shortcuts configuration.

    Loads shortcut bindings from YAML files, grouped by category.
    """

    def __init__(self, gui: Gui, validator: ConfigValidator) -> None:
        """Initialize the shortcuts loader.

        Args:
            gui: UI instance
            validator: ConfigValidator instance (unused)
        """
        self.gui = gui
        self.validator = validator

    def load(self, filepath: str) -> List[ShortcutCategoryConfig]:
        """
        Load shortcuts from a configuration file.

        Args:
            filepath: Path to shortcuts YAML file

        Returns:
            List of shortcut categories, in file order
        """
        raw_data = YamlLoader.load_file(filepath, use_splash=False)

        try:
            return _SHORTCUTS_FILE_ADAPTER.validate_python(raw_data)
        except ValidationError as e:
            raise ConfigValidationError(
                "Configuration validation failed for shortcuts file", errors=e.errors(), filepath=str(filepath)
            )
