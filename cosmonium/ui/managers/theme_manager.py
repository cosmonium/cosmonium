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

"""Theme management."""

import os
from typing import Dict, List, Optional

from ... import settings
from ...parsers.configparser import configParser
from ..skin import SkinVariant


class ThemeManager:
    """Manages UI theme and skin."""

    def __init__(
        self,
        gui,
        skin,
        variants: Optional[Dict[str, SkinVariant]],
        active_variant: Optional[str],
    ):
        """Initialize the theme manager.

        Args:
            gui: The main GUI instance
            skin: Initial skin
            variants: Mapping of variant id to SkinVariant
            active_variant: Id of the currently active variant, if any
        """
        self.gui = gui
        self.skin = skin
        self.variants = variants or {}
        self.active_variant = active_variant
        self._skin_loader = None

    def get_available_variants(self) -> List[SkinVariant]:
        """Return the skin variants declared by the current UI configuration."""
        return list(self.variants.values())

    def set_variant(self, variant_id: Optional[str]) -> None:
        """Switch to the given skin variant.

        Args:
            variant_id: Id of the variant to activate, or None to go back to the base skin's own variables

        Note:
            Variant switching is not implemented yet.
        """

    def load_skin(self, skin):
        """Load a new skin.

        Args:
            skin: Skin instance to load

        Note:
            Skin switching is not implemented yet.
        """

    def get_style(self, element):
        """Get style for a UI element.

        Args:
            element: UI element to get style for

        Returns:
            Style dictionary
        """
        return self.skin.get_style(element)

    def _get_ui_root_dir(self) -> Optional[str]:
        # TODO: Should be retrieved from app_config
        return os.path.dirname(os.path.dirname(os.path.abspath(self.gui.ui_config_file)))

    def get_available_ui_configs(self) -> List[str]:
        """List the UI configurations available under config/ui.
        The id is the directory name of every one of its subdirectories that contains a ui.yaml file.
        """
        ui_root = self._get_ui_root_dir()
        if ui_root is None or not os.path.isdir(ui_root):
            return []
        configs = []
        for entry in sorted(os.listdir(ui_root)):
            if os.path.isfile(os.path.join(ui_root, entry, 'ui.yaml')):
                configs.append(entry)
        return configs

    def get_active_ui_config(self) -> str:
        """Id of the UI configuration currently loaded."""
        return os.path.basename(os.path.dirname(os.path.abspath(self.gui.ui_config_file)))

    def get_selected_ui_config(self, _param: str) -> Optional[str]:
        """Returns the id of the configured UI.
        The id is the one stored in setting if it's available, otherwise the one actually active.
        """
        if settings.ui_config is None:
            return None
        if settings.ui_config in self.get_available_ui_configs():
            return settings.ui_config
        return self.get_active_ui_config()

    def set_selected_ui_config(self, _param: str, config_id: Optional[str]) -> None:
        """Persist the chosen UI configuration; it takes effect on the next restart.

        Args:
            config_id: Id of the UI configuration to use
        """
        settings.ui_config = config_id
        configParser.save()

    def get_selected_theme(self, _param: str) -> Optional[str]:
        return settings.ui_skin_variant

    def set_selected_theme(self, _param: str, theme_id: Optional[str]) -> None:
        """Persist the chosen UI theme; it takes effect on the next restart.

        Args:
            theme_id: Id of the UI theme to use
        """
        settings.ui_skin_variant = theme_id
        configParser.save()
