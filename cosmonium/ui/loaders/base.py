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
Base classes and interfaces for UI configuration loading.

This module provides the abstract base classes that define the interface
for widget loaders and component loaders.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from .parsers import ParsersCollection


class BaseWidgetLoader(ABC):
    """
    Abstract base class for widget loaders.

    Widget loaders are responsible for creating widget instances from
    configuration data. Each widget type should have its own loader
    that implements this interface.
    """

    @abstractmethod
    def load(self, data: Dict[str, Any], parsers: ParsersCollection, global_vars: Dict[str, Any]) -> Optional[Any]:
        """
        Load a widget from configuration data.

        Args:
            data: Dictionary containing widget configuration
            parsers: ParsersCollection instance for parsing common values
            global_vars: Dictionary of global variables for expression evaluation

        Returns:
            Widget instance or None if loading fails
        """
        ...


class BaseComponentLoader(ABC):
    """
    Abstract base class for component loaders.

    Component loaders handle loading of major UI components like menus,
    dock, HUD, skin, and shortcuts. Each component type should have its
    own loader that implements this interface.
    """

    @abstractmethod
    def load(self, filepath: str) -> Optional[Dict[str, Any]]:
        """
        Load a component from a configuration file.

        Args:
            filepath: Path to the configuration file

        Returns:
            Loaded component data structure
        """
        ...
