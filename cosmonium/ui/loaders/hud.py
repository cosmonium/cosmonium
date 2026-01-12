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
HUD loader.

This module handles loading of HUD configurations from YAML files.
"""

from panda3d.core import TextNode

from ...parsers.yamlparser import YamlParser
from ..hud.dynamictextblock import DynamicTextBlockEntries, DynamicTextBlockEntry, DynamicTextBlock
from ..templates.expression import PythonExpressionParser
from ..templates.fstring import FStringTemplateParser
from .base import BaseComponentLoader


class HUDLoader(BaseComponentLoader):
    """
    Loader for HUD configuration.

    Handles loading of HUD widgets that display dynamic text information
    with conditional visibility and templated text content.
    """

    def __init__(self, global_vars):
        """
        Initialize the HUD loader with global variables for expressions.

        Args:
            global_vars: Dictionary of global variables for expression evaluation
        """
        self.global_vars = global_vars
        self.expression_parser = PythonExpressionParser()
        self.fstring_template_parser = FStringTemplateParser()

    def load_hud_entry(self, data):
        """
        Load a HUD entry from configuration data.

        Args:
            data: Dictionary containing HUD entry configuration

        Returns:
            DynamicTextBlockEntry or DynamicTextBlockEntries instance
        """
        condition = data.get('condition')
        if condition is not None:
            condition = self.expression_parser.compile_expression(condition, self.global_vars)

        text = data.get('text')
        if text:
            # Single text entry
            title = data.get('title')
            template = self.fstring_template_parser.create_template(text)
            entry = DynamicTextBlockEntry(condition, title, template)
        else:
            # Nested entries
            entries_data = data.get('entries', [])
            entries = []
            for entry_data in entries_data:
                entry = self.load_hud_entry(entry_data)
                entries.append(entry)
            entry = DynamicTextBlockEntries(condition, entries)

        return entry

    def load_hud_entries(self, data):
        """
        Load a list of HUD entries from configuration data.

        Args:
            data: List of HUD entry configurations

        Returns:
            List of DynamicTextBlockEntry/DynamicTextBlockEntries instances
        """
        entries = []
        for entry_data in data:
            entry = self.load_hud_entry(entry_data)
            entries.append(entry)
        return entries

    def load_hud_widget(self, data):
        """
        Load a HUD widget from configuration data.

        Args:
            data: Dictionary containing HUD widget configuration

        Returns:
            Tuple of (DynamicTextBlock instance, anchor_name)
        """
        id_ = data.get('id')
        anchor_name = data.get('anchor')
        size = data.get('size', 5)

        # Determine alignment and direction based on anchor position
        if anchor_name == 'top-left':
            align = TextNode.A_left
            down = True
        elif anchor_name == 'top-right':
            align = TextNode.A_right
            down = True
        elif anchor_name == 'bottom-left':
            align = TextNode.A_left
            down = False
        elif anchor_name == 'bottom-right':
            align = TextNode.A_right
            down = False
        else:
            # Default to top-left
            align = TextNode.A_left
            down = True

        entries = self.load_hud_entries(data.get('entries'))
        widget = DynamicTextBlock(id_, align=align, down=down, count=size, entries=entries)
        return widget, anchor_name

    def load_hud_widgets(self, data):
        """
        Load HUD widgets from configuration data.

        Args:
            data: List of HUD widget configurations

        Returns:
            Dictionary mapping anchor names to lists of widgets
        """
        hud = {}
        for widget_data in data:
            widget, anchor_name = self.load_hud_widget(widget_data)
            hud.setdefault(anchor_name, []).append(widget)
        return hud

    def load(self, filepath):
        """
        Load HUD configuration from a YAML file.

        Args:
            filepath: Path to HUD YAML file

        Returns:
            Dictionary mapping anchor names to lists of DynamicTextBlock widgets
        """
        parser = YamlParser()
        data = parser.load_and_parse(filepath)
        hud = self.load_hud_widgets(data.get('hud', []))
        return hud
