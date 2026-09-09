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
Widget parsers for dock widget configuration.

Dock widget type dispatch (button/text/spacer/layout) is built on
`TypedYamlParser`, the same type-registry dispatch mechanism used by the
universe object parsers (`ObjectYamlParser` and friends), so both
infrastructures share one polymorphic-node dispatch pattern instead of two.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from ...parsers.yamlparser import TypedYamlParser, YamlModuleParser
from ..config.models import (
    ButtonWidgetConfig,
    ContainerLayoutConfig,
    LayoutWidgetConfig,
    OptionMenuWidgetConfig,
    SearchWidgetConfig,
    SpacerWidgetConfig,
    TextWidgetConfig,
    WidgetLayoutConfig,
)
from ..dock.button import ButtonDockWidget
from ..dock.layouts import LayoutDockWidget, SpaceDockWidget
from ..dock.option_menu import OptionMenuDockWidget
from ..dock.search import SearchDockWidget
from ..dock.text import TextDockWidget
from ..templates.expression import PythonExpressionParser
from ..templates.fstring import FStringTemplateParser
from .parsers import ParsersCollection


def widget_layout_kwargs(data: WidgetLayoutConfig) -> Dict[str, Any]:
    """
    Extract the layout parameters shared by every dock widget from its configuration.

    Args:
        data: The configuration of the widget, a `WidgetLayoutConfig` model

    Returns:
        The keyword arguments to pass to the widget constructor
    """
    parsers = ParsersCollection.get_instance()
    return {
        'align': parsers.alignment.parse(data.align),
        'justify': parsers.alignment.parse(data.justify),
        'margin': parsers.length.parse_edge_lengths(data.margin),
        'grow': data.grow,
        'class_': data.class_,
        'id_': data.id,
    }


def container_layout_kwargs(data: ContainerLayoutConfig) -> Dict[str, Any]:
    """
    Extract the layout parameters of a widget laying out children from its configuration.

    Args:
        data: The configuration of the container, a `ContainerLayoutConfig` model

    Returns:
        The keyword arguments to pass to the container constructor
    """
    parsers = ParsersCollection.get_instance()
    return {
        'padding': parsers.length.parse_edge_lengths(data.padding),
        'gap': parsers.length.parse_gap(data.gap),
    }


class WidgetYamlParser(TypedYamlParser):
    """Widgets registry for dock widgets"""


class ButtonWidgetLoader(YamlModuleParser):
    """
    Loader for button widgets.

    Handles loading of button dock widgets with text or icon codes.
    """

    def __init__(self):
        """
        Initialize the button widget loader with an expression parser for 'checked'.
        """
        self.expression_parser = PythonExpressionParser()

    def decode(self, data: ButtonWidgetConfig, global_vars: Optional[Dict[str, Any]] = None) -> ButtonDockWidget:
        """
        Load a button widget from configuration data.

        Args:
            widget_config: ButtonWidgetConfig Pydantic model
            global_vars: Dictionary of global variables for expression evaluation

        Returns:
            ButtonDockWidget instance
        """
        if data.text:
            text = data.text
            is_icon = False
            rescale = False
        elif data.code:
            code = int(data.code, 16)
            text = chr(code)
            is_icon = True
            rescale = data.rescale
        else:
            text = None
            is_icon = False

        if data.code_checked:
            text_checked = chr(int(data.code_checked, 16))
        else:
            text_checked = data.text_checked

        if data.checked is not None:
            checked = self.expression_parser.compile_expression(data.checked, global_vars)
        else:
            checked = None

        if data.enabled is not None:
            enabled = self.expression_parser.compile_expression(data.enabled, global_vars)
        else:
            enabled = None

        return ButtonDockWidget(
            text,
            data.event,
            menu=data.menu,
            is_icon=is_icon,
            rescale=rescale,
            text_checked=text_checked,
            checked=checked,
            enabled=enabled,
            **widget_layout_kwargs(data),
        )


class OptionMenuWidgetLoader(YamlModuleParser):
    """
    Loader for option-menu widgets.

    Handles loading of dock widgets that show a DirectOptionMenu dropdown.
    """

    def __init__(self):
        """
        Initialize the option-menu widget loader with an expression parser.
        """
        self.expression_parser = PythonExpressionParser()

    def decode(self, data: OptionMenuWidgetConfig, global_vars: Dict[str, Any]) -> OptionMenuDockWidget:
        """
        Load an option-menu widget from configuration data.

        Args:
            data: OptionMenuWidgetConfig Pydantic model
            global_vars: Dictionary of global variables for expression evaluation

        Returns:
            OptionMenuDockWidget instance
        """
        selected = None
        if data.selected is not None:
            selected = self.expression_parser.compile_expression(data.selected, global_vars)

        enabled = None
        if data.enabled is not None:
            enabled = self.expression_parser.compile_expression(data.enabled, global_vars)

        return OptionMenuDockWidget(
            data.items,
            data.event,
            selected=selected,
            enabled=enabled,
            **widget_layout_kwargs(data),
        )


class TextWidgetLoader(YamlModuleParser):
    """
    Loader for text widgets.

    Handles loading of text dock widgets with alignment and styling.
    """

    def __init__(self):
        """
        Initialize the text widget loader with template parser.
        """
        self.fstring_template_parser = FStringTemplateParser()

    def decode(self, data: TextWidgetConfig, global_vars: Optional[Dict[str, Any]] = None) -> TextDockWidget:
        """
        Load a text widget from configuration data.

        Args:
            widget_config: TextWidgetConfig Pydantic model
            global_vars: Dictionary of global variables for expression evaluation

        Returns:
            TextDockWidget instance
        """
        parsers = ParsersCollection.get_instance()
        template = self.fstring_template_parser.create_template(data.text)

        return TextDockWidget(
            template,
            text_align=parsers.text_alignment.parse(data.text_align),
            **widget_layout_kwargs(data),
        )


class SearchWidgetLoader(YamlModuleParser):
    """
    Loader for search widgets.

    Handles loading of quick-search dock widgets.
    """

    def decode(self, data: SearchWidgetConfig, global_vars: Optional[Dict[str, Any]] = None) -> SearchDockWidget:
        """
        Load a search widget from configuration data.

        Args:
            widget_config: SearchWidgetConfig Pydantic model
            global_vars: Dictionary of global variables for expression evaluation

        Returns:
            SearchDockWidget instance
        """

        return SearchDockWidget(
            placeholder=data.placeholder,
            width=data.width,
            max_results=data.max_results,
            **widget_layout_kwargs(data),
        )


class SpacerWidgetLoader(YamlModuleParser):
    """
    Loader for spacer widgets.

    Handles loading of spacer dock widgets used for layout spacing.
    """

    def decode(self, data: SpacerWidgetConfig, global_vars: Optional[Dict[str, Any]] = None) -> SpaceDockWidget:
        """
        Load a spacer widget from configuration data.

        Args:
            widget_config: SpacerWidgetConfig Pydantic model
            global_vars: Dictionary of global variables for expression evaluation

        Returns:
            SpaceDockWidget instance
        """
        parsers = ParsersCollection.get_instance()
        width, height = (None, None) if data.size is None else data.size

        return SpaceDockWidget(
            width=parsers.length.parse(width),
            height=parsers.length.parse(height),
            **widget_layout_kwargs(data),
        )


class LayoutWidgetLoader(YamlModuleParser):
    """
    Loader for layout widgets.

    Handles loading of layout dock widgets that contain child widgets.
    This loader recursively loads child widgets through `WidgetYamlParser`.
    """

    def decode(self, data: LayoutWidgetConfig, global_vars: Optional[Dict[str, Any]] = None) -> LayoutDockWidget:
        """
        Load a layout widget from configuration data.

        Args:
            widget_config: LayoutWidgetConfig Pydantic model
            global_vars: Dictionary of global_vars for expression evaluation

        Returns:
            LayoutDockWidget instance
        """
        # Recursively load child widgets
        widgets = []
        for child_widget_config in data.widgets:
            widget = WidgetYamlParser.decode_object(child_widget_config, global_vars=global_vars)
            if widget is not None:
                widgets.append(widget)

        return LayoutDockWidget(
            data.orientation,
            widgets,
            **container_layout_kwargs(data),
            **widget_layout_kwargs(data),
        )
