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
Skin loader.

This module handles loading of UI skin configurations from YAML files.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List

from ...parsers.yamlparser import YamlParser
from ..config.models import SkinEntryConfig, SkinSelectorConfig
from ..skin import ParentSelector, Selector, UISkin, UISkinEntry
from .base import BaseComponentLoader
from .parsers import ParsersCollection

if TYPE_CHECKING:
    from ..config.validator import ConfigValidator
    from ..gui import Gui


class SkinLoader(BaseComponentLoader):
    """
    Loader for UI skin configuration.

    Handles loading of UI skin entries that define visual styling for
    UI elements including colors, fonts, margins, padding, and sizes.
    """

    def __init__(self, gui: Gui, validator: ConfigValidator) -> None:
        """Initialize the skin loader with parsers.

        Args:
            gui: UI instance
            validator: ConfigValidator instance
        """
        self.gui = gui
        self.validator = validator
        self.parsers = ParsersCollection()

    def load_skin_selector(self, selector_config: SkinSelectorConfig) -> Any:
        """
        Load a CSS-like selector from configuration data.

        Args:
            selector_config: SkinSelectorConfig Pydantic model

        Returns:
            Selector or ParentSelector instance
        """

        selector = Selector(selector_config.element, selector_config.state, selector_config.class_, selector_config.id)

        if selector_config.parent is not None:
            parent_selector = self.load_skin_selector(selector_config.parent)
            selector = ParentSelector(parent_selector, selector)

        return selector

    def load_skin_entry(self, entry_config: SkinEntryConfig) -> UISkinEntry:
        """
        Load a skin entry from configuration data.

        Args:
            entry_config: SkinEntryConfig Pydantic model

        Returns:
            UISkinEntry instance
        """
        # Load selector
        selector = self.load_skin_selector(entry_config)
        entry = UISkinEntry(selector, {})

        # Parse colors using Pydantic model fields
        entry.background_color = self.parsers.color.parse(entry_config.background_color)
        entry.text_color = self.parsers.color.parse(entry_config.text_color)
        entry.border_color = self.parsers.color.parse(entry_config.border_color)

        # Parse font properties
        entry.font_family = entry_config.font_family
        entry.font_size = self.parsers.length.parse(entry_config.font_size, entry)
        entry.font_style = entry_config.font_style
        entry.font_weight = entry_config.font_weight

        # Parse layout properties
        entry.margin = self.parsers.length.parse_edge_lengths(entry_config.margin, entry)
        entry.padding = self.parsers.length.parse_edge_lengths(entry_config.padding, entry)
        entry.width = self.parsers.length.parse(entry_config.width, entry)
        entry.height = self.parsers.length.parse(entry_config.height, entry)

        return entry

    def load_skin_entries(self, data: List[Any]) -> UISkin:
        """
        Load skin entries from configuration data.

        Args:
            data: List of skin entry configurations

        Returns:
            UISkin instance
        """
        skin = UISkin()
        for entry_data in data:
            validated = self.validator.validate_dict(entry_data, SkinEntryConfig)
            entry = self.load_skin_entry(validated)
            skin.add_entry(entry)
        return skin

    def load(self, filepath: str) -> UISkin:
        """
        Load skin configuration from a YAML file.

        Args:
            filepath: Path to skin YAML file

        Returns:
            UISkin instance
        """
        parser = YamlParser()
        data = parser.load_and_parse(filepath)
        skin = self.load_skin_entries(data)
        return skin
