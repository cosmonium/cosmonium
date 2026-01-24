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

from ...parsers.yamlparser import YamlParser
from ..skin import ParentSelector, Selector, UISkinEntry, UISkin
from .base import BaseComponentLoader
from .parsers import ParsersCollection


class SkinLoader(BaseComponentLoader):
    """
    Loader for UI skin configuration.

    Handles loading of UI skin entries that define visual styling for
    UI elements including colors, fonts, margins, padding, and sizes.
    """

    def __init__(self, gui):
        """Initialize the skin loader with parsers.

        Args:
            gui: UI instance
        """
        self.gui = gui
        self.parsers = ParsersCollection()

    def load_skin_selector(self, data):
        """
        Load a CSS-like selector from configuration data.

        Args:
            data: Dictionary containing selector configuration

        Returns:
            Selector or ParentSelector instance
        """
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
        """
        Load a skin entry from configuration data.

        Args:
            data: Dictionary containing skin entry configuration

        Returns:
            UISkinEntry instance
        """
        selector = self.load_skin_selector(data)
        entry = UISkinEntry(selector, {})

        # Parse colors
        entry.background_color = self.parsers.color.parse(data.get('background-color'))
        entry.text_color = self.parsers.color.parse(data.get('text-color'))
        entry.border_color = self.parsers.color.parse(data.get('border-color'))

        # Parse font properties
        entry.font_family = data.get('font-family')
        entry.font_size = self.parsers.length.parse(data.get('font-size'), entry)
        entry.font_style = data.get('font-style')
        entry.font_weight = data.get('font-weight')

        # Parse layout properties
        entry.margin = self.parsers.length.parse_edge_lengths(data.get('margin'), entry)
        entry.padding = self.parsers.length.parse_edge_lengths(data.get('padding'), entry)
        entry.width = self.parsers.length.parse(data.get('width'), entry)
        entry.height = self.parsers.length.parse(data.get('height'), entry)

        return entry

    def load_skin_entries(self, data):
        """
        Load skin entries from configuration data.

        Args:
            data: List of skin entry configurations

        Returns:
            UISkin instance
        """
        skin = UISkin()
        for entry_data in data:
            entry = self.load_skin_entry(entry_data)
            skin.add_entry(entry)
        return skin

    def load(self, filepath):
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
