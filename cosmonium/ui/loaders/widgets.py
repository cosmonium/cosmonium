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
Widget loader registry and widget-specific loaders.

This module implements the registry pattern for widget loaders, allowing
new widget types to be registered dynamically without modifying core code.
"""

from ..dock.button import ButtonDockWidget
from ..dock.layouts import LayoutDockWidget, SpaceDockWidget
from ..dock.text import TextDockWidget
from ..templates.fstring import FStringTemplateParser

from .base import BaseWidgetLoader
from .parsers import ParsersCollection


class WidgetLoaderRegistry:
    """
    Registry for widget loaders.

    The registry maintains a mapping of widget type names to their
    corresponding loader instances. This allows dynamic dispatch of
    widget loading based on the 'type' field in configuration data.
    """

    _instance = None

    def __init__(self):
        """
        Initialize the registry with a parser collection.
        """
        self._parsers = ParsersCollection.get_instance()
        self._loaders = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, widget_type, loader):
        """
        Register a widget loader for a specific type.

        Args:
            widget_type: String identifier for the widget type
            loader: BaseWidgetLoader instance to handle this widget type

        Example:
            registry.register('button', ButtonWidgetLoader())
        """
        if not isinstance(loader, BaseWidgetLoader):
            raise TypeError(f"Loader must be an instance of BaseWidgetLoader, got {type(loader)}")
        self._loaders[widget_type] = loader

    def load(self, data, global_vars):
        """
        Load a widget from configuration data.

        Args:
            data: Dictionary containing widget configuration with 'type' field
            global_vars: Dictionary of global variables for expression evaluation

        Returns:
            Widget instance or None if loading fails
        """
        widget_type = data.get('type')
        if widget_type not in self._loaders:
            print(f"Unsupported widget type: {widget_type}")
            return None

        loader = self._loaders[widget_type]
        return loader.load(data, self._parsers, global_vars)


class ButtonWidgetLoader(BaseWidgetLoader):
    """
    Loader for button widgets.

    Handles loading of button dock widgets with text or icon codes.
    """

    def load(self, data, parsers, global_vars):
        """
        Load a button widget from configuration data.

        Args:
            data: Configuration dictionary containing button parameters
            parsers: ParsersCollection instance
            global_vars: Dictionary of global variables for expression evaluation

        Returns:
            ButtonDockWidget instance
        """
        alignments = parsers.alignment.parse(data.get('align'))
        borders = parsers.border.parse(data.get('borders'))

        if 'text' in data:
            text = data.get('text')
            rescale = False
        elif 'code' in data:
            code = int(data['code'], 16)
            text = chr(code)
            rescale = data.get('rescale', True)
        else:
            text = None

        event = data.get('event')
        size = data.get('size', None)

        return ButtonDockWidget(text, event, size, rescale=rescale, alignments=alignments, borders=borders)


class TextWidgetLoader(BaseWidgetLoader):
    """
    Loader for text widgets.

    Handles loading of text dock widgets with alignment and styling.
    """

    def __init__(self):
        """
        Initialize the text widget loader with template parser.
        """
        self.fstring_template_parser = FStringTemplateParser()

    def load(self, data, parsers, global_vars):
        """
        Load a text widget from configuration data.

        Args:
            data: Configuration dictionary containing text parameters
            parsers: ParsersCollection instance
            global_vars: Dictionary of global variables for expression evaluation

        Returns:
            TextDockWidget instance
        """
        alignments = parsers.alignment.parse(data.get('align'))
        borders = parsers.border.parse(data.get('borders'))
        text = data.get('text')
        template = self.fstring_template_parser.create_template(text)
        align = parsers.text_alignment.parse(data.get('align'))

        return TextDockWidget(template, align=align, alignments=alignments, borders=borders)


class SpacerWidgetLoader(BaseWidgetLoader):
    """
    Loader for spacer widgets.

    Handles loading of spacer dock widgets used for layout spacing.
    """

    def load(self, data, parsers, global_vars):
        """
        Load a spacer widget from configuration data.

        Args:
            data: Configuration dictionary containing spacer parameters
            parsers: ParsersCollection instance
            global_vars: Dictionary of global variables for expression evaluation

        Returns:
            SpaceDockWidget instance
        """
        alignments = parsers.alignment.parse(data.get('align'), ("min", "min"))
        size = tuple(data.get('size', (0, 0)))

        return SpaceDockWidget(size=size, alignments=alignments, borders=None)


class LayoutWidgetLoader(BaseWidgetLoader):
    """
    Loader for layout widgets.

    Handles loading of layout dock widgets that contain child widgets.
    This loader recursively loads child widgets using the registry.
    """

    def load(self, data, parsers, global_vars):
        """
        Load a layout widget from configuration data.

        Args:
            data: Configuration dictionary containing layout parameters
            parsers: ParsersCollection instance
            global_vars: Dictionary of global variables for expression evaluation

        Returns:
            LayoutDockWidget instance
        """
        alignments = parsers.alignment.parse(data.get('align'))
        borders = parsers.border.parse(data.get('borders'))
        gaps = parsers.gap.parse(data.get('gaps'))
        size = data.get('size', 32)
        decoration_size = data.get('decoration-size', (1, 1))
        rounded_corners = data.get('rounded-corners', 0)
        orientation = data.get('orientation', 'horizontal')

        # Recursively load child widgets
        registry = WidgetLoaderRegistry.get_instance()
        widgets = []
        for widget_data in data.get('widgets', []):
            widget = registry.load(widget_data, global_vars)
            if widget is not None:
                widgets.append(widget)

        return LayoutDockWidget(
            size,
            orientation,
            widgets,
            decoration_size=decoration_size,
            rounded_corners=rounded_corners,
            alignments=alignments,
            borders=borders,
            gaps=gaps,
        )
