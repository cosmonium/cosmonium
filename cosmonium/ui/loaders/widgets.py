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
    LayoutWidgetConfig,
    OptionMenuWidgetConfig,
    SpacerWidgetConfig,
    TextWidgetConfig,
)
from ..dock.button import ButtonDockWidget
from ..dock.layouts import LayoutDockWidget, SpaceDockWidget
from ..dock.option_menu import OptionMenuDockWidget
from ..dock.text import TextDockWidget
from ..templates.expression import PythonExpressionParser
from ..templates.fstring import FStringTemplateParser
from .parsers import ParsersCollection


class WidgetYamlParser(TypedYamlParser):
    """Widgets registry for dock widgets"""


class ButtonWidgetLoader(YamlModuleParser):
    """
    Loader for button widgets.

    Handles loading of button dock widgets with text or icon codes.
    """

    def decode(self, data: ButtonWidgetConfig, global_vars: Optional[Dict[str, Any]] = None) -> ButtonDockWidget:
        """
        Load a button widget from configuration data.

        Args:
            widget_config: ButtonWidgetConfig Pydantic model
            global_vars: Dictionary of global variables for expression evaluation

        Returns:
            ButtonDockWidget instance
        """
        parsers = ParsersCollection.get_instance()
        alignments = parsers.alignment.parse(data.align)
        borders = parsers.border.parse(data.borders)

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

        return ButtonDockWidget(
            text,
            data.event,
            menu=data.menu,
            is_icon=is_icon,
            rescale=rescale,
            alignments=alignments,
            borders=borders,
            class_=data.class_,
            id_=data.id,
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
        parsers = ParsersCollection.get_instance()
        alignments = parsers.alignment.parse(data.align)
        borders = parsers.border.parse(data.borders)

        selected = None
        if data.selected is not None:
            selected = self.expression_parser.compile_expression(data.selected, global_vars)

        return OptionMenuDockWidget(
            data.items,
            data.event,
            selected=selected,
            alignments=alignments,
            borders=borders,
            class_=data.class_,
            id_=data.id,
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
        borders = parsers.border.parse(data.borders)
        template = self.fstring_template_parser.create_template(data.text)
        align = parsers.text_alignment.parse(data.align)

        return TextDockWidget(
            template,
            align=align,
            borders=borders,
            class_=data.class_,
            id_=data.id,
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
        alignments = parsers.alignment.parse(data.align)
        # A spacer has no skin entry of its own (yet), the lengths are resolved using the layout contaoining it.
        width = parsers.length.parse(data.size[0])
        height = parsers.length.parse(data.size[1])

        return SpaceDockWidget(width, height, alignments=alignments, borders=None)


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
        parsers = ParsersCollection.get_instance()
        alignments = parsers.alignment.parse(data.align)
        borders = parsers.border.parse(data.borders)
        gaps = parsers.gap.parse(data.gaps)

        # Recursively load child widgets
        widgets = []
        for child_widget_config in data.widgets:
            widget = WidgetYamlParser.decode_object(child_widget_config, global_vars=global_vars)
            if widget is not None:
                widgets.append(widget)

        return LayoutDockWidget(
            data.orientation,
            widgets,
            alignments=alignments,
            borders=borders,
            gaps=gaps,
            class_=data.class_,
            id_=data.id,
        )
