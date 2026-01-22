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
from copy import deepcopy


"""
Dock loader.

This module handles loading of dock widget configurations from YAML files.
"""

from ...parsers.yamlparser import YamlParser

from ..dock.dock import Dock
from .base import BaseComponentLoader
from .widgets import WidgetLoaderRegistry


class DockLoader(BaseComponentLoader):
    """
    Loader for dock widget configuration.

    Handles loading of dock widgets which are displayed at screen edges
    and contain button, text, and layout widgets.
    """

    def __init__(self, gui, global_vars):
        """
        Initialize the Dock loader with global variables for expressions.

        Args:
            global_vars: Dictionary of global variables for expression evaluation
        """
        self.gui = gui
        self.global_vars = global_vars

    def load_dock_config(self, data):
        """
        Load dock configuration from parsed YAML data.

        Args:
            data: Dictionary containing dock configuration
            global_vars: Dictionary of global variables for expression evaluation

        Returns:
            Tuple of (layout_widget, orientation, location)
        """
        id_ = data.get('id', None)
        orientation = data.get('orientation', 'horizontal')
        location = data.get('location', 'bottom')

        # Create a layout widget configuration from dock data
        layout_data = deepcopy(data)
        layout_data['type'] = 'layout'
        layout_data['orientation'] = orientation

        widget_registry = WidgetLoaderRegistry.get_instance()
        layout = widget_registry.load(layout_data, self.global_vars)
        dock = Dock(id_, orientation, location, layout, self.gui)
        return dock

    def load(self, filepath):
        """
        Load dock configuration from a YAML file.

        Args:
            filepath: Path to dock YAML file

        Returns:
            Tuple of (layout_widget, orientation, location)
        """
        parser = YamlParser()
        data = parser.load_and_parse(filepath)
        docks = []
        for dock_config in data.get('dock'):
            dock = self.load_dock_config(dock_config)
            docks.append(dock)
        return docks
