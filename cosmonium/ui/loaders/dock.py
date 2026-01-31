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
Dock loader.

This module handles loading of dock widget configurations from YAML files.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from ...parsers.yamlparser import YamlParser
from ..config.models import DockConfig, LayoutWidgetConfig
from ..dock.dock import Dock
from .base import BaseComponentLoader
from .widgets import WidgetLoaderRegistry

if TYPE_CHECKING:
    from ..config.validator import ConfigValidator
    from ..gui import Gui


class DockLoader(BaseComponentLoader):
    """
    Loader for dock widget configuration.

    Handles loading of dock widgets which are displayed at screen edges
    and contain button, text, and layout widgets.
    """

    def __init__(self, gui: Gui, validator: ConfigValidator) -> None:
        """
        Initialize the Dock loader with global variables for expressions.

        Args:
            gui: UI instance
            validator: ConfigValidator instance
        """
        self.gui = gui
        self.validator = validator

    def load_dock_config(self, data: Dict[str, Any]) -> Dock:
        """
        Load dock configuration from parsed YAML data.

        Args:
            data: Dictionary containing dock configuration

        Returns:
            Dock instance
        """
        # Validate dock configuration
        validated = self.validator.validate_dict(data, DockConfig)

        # Create a LayoutWidgetConfig from the dock for widget loading
        layout_data = {
            'type': 'layout',
            'orientation': validated.orientation,
            'widgets': validated.widgets,
            'size': validated.size,
            'gaps': validated.gaps,
            'borders': validated.borders,
            'decoration-size': validated.decoration_size,
            'rounded-corners': validated.rounded_corners,
        }
        layout_config = LayoutWidgetConfig(**layout_data)

        widget_registry = WidgetLoaderRegistry.get_instance()
        layout = widget_registry.load(layout_config, self.gui)
        dock = Dock(validated.id, validated.orientation, validated.anchor, layout)

        return dock

    def load(self, filepath: str) -> List[Dock]:
        """
        Load dock configuration from a YAML file.

        Args:
            filepath: Path to dock YAML file

        Returns:
            List of dock widgets
        """
        parser = YamlParser()
        data = parser.load_and_parse(filepath)
        docks = []
        for dock_config in data.get('dock'):
            dock = self.load_dock_config(dock_config)
            docks.append(dock)
        return docks
