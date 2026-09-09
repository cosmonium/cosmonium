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
Init module to register all the default loaders.
"""

from ..config.models import (
    ButtonWidgetConfig,
    LayoutWidgetConfig,
    OptionMenuWidgetConfig,
    SearchWidgetConfig,
    SpacerWidgetConfig,
    TextWidgetConfig,
)
from .widgets import (
    ButtonWidgetLoader,
    LayoutWidgetLoader,
    OptionMenuWidgetLoader,
    SearchWidgetLoader,
    SpacerWidgetLoader,
    TextWidgetLoader,
    WidgetYamlParser,
)


def init_widget_loaders():
    """Register all default widget loaders."""

    WidgetYamlParser.register_parser('button', ButtonWidgetLoader(), ButtonWidgetConfig)
    WidgetYamlParser.register_parser('layout', LayoutWidgetLoader(), LayoutWidgetConfig)
    WidgetYamlParser.register_parser('option-menu', OptionMenuWidgetLoader(), OptionMenuWidgetConfig)
    WidgetYamlParser.register_parser('search', SearchWidgetLoader(), SearchWidgetConfig)
    WidgetYamlParser.register_parser('spacer', SpacerWidgetLoader(), SpacerWidgetConfig)
    WidgetYamlParser.register_parser('text', TextWidgetLoader(), TextWidgetConfig)
