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

from ..config.models import ButtonWidgetConfig, LayoutWidgetConfig, SpacerWidgetConfig, TextWidgetConfig
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

    def load(self, widget_config, global_vars):
        """
        Load a widget from configuration data.

        Args:
            widget_config: WidgetConfig Pydantic model
            global_vars: Dictionary of global variables for expression evaluation

        Returns:
            Widget instance or None if loading fails
        """

        # Get widget type from Pydantic model
        widget_type = widget_config.type

        if widget_type not in self._loaders:
            raise NotImplementedError(f"Unsupported widget type: {widget_type}")

        loader = self._loaders[widget_type]
        return loader.load(widget_config, self._parsers, global_vars)


class ButtonWidgetLoader(BaseWidgetLoader):
    """
    Loader for button widgets.

    Handles loading of button dock widgets with text or icon codes.
    """

    def load(self, widget_config: ButtonWidgetConfig, parsers, global_vars):
        """
        Load a button widget from configuration data.

        Args:
            widget_config: ButtonWidgetConfig Pydantic model
            parsers: ParsersCollection instance
            global_vars: Dictionary of global variables for expression evaluation

        Returns:
            ButtonDockWidget instance
        """
        alignments = parsers.alignment.parse(widget_config.align)
        borders = parsers.border.parse(widget_config.borders)

        if widget_config.text:
            text = widget_config.text
            rescale = False
        elif widget_config.code:
            code = int(widget_config.code, 16)
            text = chr(code)
            rescale = widget_config.rescale
        else:
            text = None

        return ButtonDockWidget(
            text, widget_config.event, widget_config.size, rescale=rescale, alignments=alignments, borders=borders
        )


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

    def load(self, widget_config: TextWidgetConfig, parsers, global_vars):
        """
        Load a text widget from configuration data.

        Args:
            widget_config: TextWidgetConfig Pydantic model
            parsers: ParsersCollection instance
            global_vars: Dictionary of global variables for expression evaluation

        Returns:
            TextDockWidget instance
        """
        alignments = parsers.alignment.parse(widget_config.align)
        borders = parsers.border.parse(widget_config.borders)
        template = self.fstring_template_parser.create_template(widget_config.text)
        align = parsers.text_alignment.parse(widget_config.align)

        return TextDockWidget(template, align=align, alignments=alignments, borders=borders)


class SpacerWidgetLoader(BaseWidgetLoader):
    """
    Loader for spacer widgets.

    Handles loading of spacer dock widgets used for layout spacing.
    """

    def load(self, widget_config: SpacerWidgetConfig, parsers, global_vars):
        """
        Load a spacer widget from configuration data.

        Args:
            widget_config: SpacerWidgetConfig Pydantic model
            parsers: ParsersCollection instance
            global_vars: Dictionary of global variables for expression evaluation

        Returns:
            SpaceDockWidget instance
        """
        alignments = parsers.alignment.parse(widget_config.align, ("min", "min"))
        size = tuple(widget_config.size)

        return SpaceDockWidget(size=size, alignments=alignments, borders=None)


class LayoutWidgetLoader(BaseWidgetLoader):
    """
    Loader for layout widgets.

    Handles loading of layout dock widgets that contain child widgets.
    This loader recursively loads child widgets using the registry.
    """

    def load(self, widget_config: LayoutWidgetConfig, parsers, global_vars):
        """
        Load a layout widget from configuration data.

        Args:
            widget_config: LayoutWidgetConfig Pydantic model
            parsers: ParsersCollection instance
            global_vars: Dictionary of global_vars for expression evaluation

        Returns:
            LayoutDockWidget instance
        """
        alignments = parsers.alignment.parse(widget_config.align)
        borders = parsers.border.parse(widget_config.borders)
        gaps = parsers.gap.parse(widget_config.gaps)
        decoration_size = widget_config.decoration_size
        rounded_corners = widget_config.rounded_corners

        # Recursively load child widgets
        registry = WidgetLoaderRegistry.get_instance()
        widgets = []
        for child_widget_config in widget_config.widgets:
            widget = registry.load(child_widget_config, global_vars)
            if widget is not None:
                widgets.append(widget)

        return LayoutDockWidget(
            widget_config.size,
            widget_config.orientation,
            widgets,
            decoration_size=decoration_size,
            rounded_corners=rounded_corners,
            alignments=alignments,
            borders=borders,
            gaps=gaps,
        )
