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

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List

from panda3d.core import TextNode

from ...parsers.yamlparser import YamlParser
from ..config.models import HUDWidgetConfig
from ..hud.dynamictextblock import DynamicTextBlock, DynamicTextBlockEntries, DynamicTextBlockEntry
from ..templates.expression import PythonExpressionParser
from ..templates.fstring import FStringTemplateParser
from .base import BaseComponentLoader

if TYPE_CHECKING:
    from ..config.validator import ConfigValidator
    from ..gui import Gui


class HUDLoader(BaseComponentLoader):
    """
    Loader for HUD configuration.

    Handles loading of HUD widgets that display dynamic text information
    with conditional visibility and templated text content.
    """

    def __init__(self, gui: Gui, validator: ConfigValidator) -> None:
        """
        Initialize the HUD loader with global variables for expressions.

        Args:
            gui: UI instance
            validator: ConfigValidator instance
        """
        self.gui = gui
        self.validator = validator
        self.expression_parser = PythonExpressionParser()
        self.fstring_template_parser = FStringTemplateParser()

    def load_hud_entry(self, entry_config: Any) -> Any:
        """
        Load a HUD entry from configuration data.

        Args:
            entry_config: HUDEntryConfig Pydantic model

        Returns:
            DynamicTextBlockEntry or DynamicTextBlockEntries instance
        """
        if entry_config.condition is not None:
            condition = self.expression_parser.compile_expression(entry_config.condition, self.gui.global_vars.globals)
        else:
            condition = None

        if entry_config.text:
            # Single text entry
            template = self.fstring_template_parser.create_template(entry_config.text)
            entry = DynamicTextBlockEntry(condition, entry_config.title, template)
        else:
            # Nested entries
            entries = []
            for nested_entry_config in entry_config.entries:
                entry = self.load_hud_entry(nested_entry_config)
                entries.append(entry)
            entry = DynamicTextBlockEntries(condition, entries)

        return entry

    def load_hud_entries(self, data: List[Any]) -> List[Any]:
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

    def load_hud_widget(self, data: Any) -> DynamicTextBlock:
        """
        Load a HUD widget from configuration data.

        Args:
            data: HUD widget configuration

        Returns:
            DynamicTextBlock instance
        """

        # Determine alignment and direction based on anchor position
        if data.anchor == 'top-left':
            align = TextNode.A_left
            down = True
        elif data.anchor == 'top-right':
            align = TextNode.A_right
            down = True
        elif data.anchor == 'bottom-left':
            align = TextNode.A_left
            down = False
        elif data.anchor == 'bottom-right':
            align = TextNode.A_right
            down = False
        else:
            # Default to top-left
            align = TextNode.A_left
            down = True

        # Load entries from Pydantic model
        entries = self.load_hud_entries(data.entries)

        widget = DynamicTextBlock(
            data.id, location=data.anchor, align=align, down=down, count=data.size, entries=entries
        )
        return widget

    def load_hud_widgets(self, data: List[Any]) -> List[DynamicTextBlock]:
        """
        Load HUD widgets from configuration data.

        Args:
            data: List of HUD widget configurations

        Returns:
            Dictionary mapping anchor names to lists of widgets
        """
        hud = []
        for widget_data in data:
            # Validate HUD widget configuration
            validated = self.validator.validate_dict(widget_data, HUDWidgetConfig)
            widget = self.load_hud_widget(validated)
            hud.append(widget)
        return hud

    def load(self, filepath: str) -> List[DynamicTextBlock]:
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
