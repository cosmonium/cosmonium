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
First-run tips loader.

This module handles loading of the first-run tips shown to new users from
configuration files.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from ...parsers.yamlloader import YamlLoader
from ..config.models import TipConfig
from .base import BaseComponentLoader

if TYPE_CHECKING:
    from ...parsers.validator import ConfigValidator
    from ..gui import Gui


class TipsLoader(BaseComponentLoader):
    """
    Loader for first-run tips configuration.

    Loads the ordered list of tips shown once to new users, the first time a
    given UI configuration is used.
    """

    def __init__(self, gui: Gui, validator: ConfigValidator) -> None:
        """
        Initialize the tips loader.

        Args:
            gui: UI instance
            validator: ConfigValidator instance
        """
        self.gui = gui
        self.validator = validator

    def load(self, filepath: str) -> List[TipConfig]:
        """
        Load the first-run tips from a configuration file.

        Args:
            filepath: Path to tips YAML file

        Returns:
            Ordered list of TipConfig instances
        """
        data = YamlLoader.load_file(filepath, use_splash=False)
        tips = []
        for tip_data in data.get('tips', []):
            validated = self.validator.validate_dict(tip_data, TipConfig)
            tips.append(validated)
        return tips
