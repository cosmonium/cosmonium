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


class ThemeManager:
    """Manages UI theme and skin."""

    def __init__(self, gui, skin):
        """Initialize the theme manager.

        Args:
            gui: The main GUI instance
            skin: Initial skin
        """
        self.gui = gui
        self.skin = skin

    def load_skin(self, skin):
        """Load a new skin.

        Args:
            skin: Skin instance to load
        """
        # TODO: Skin switch not implemented
        self.skin = skin

    def get_style(self, element):
        """Get style for a UI element.

        Args:
            element: UI element to get style for

        Returns:
            Style dictionary
        """
        return self.skin.get_style(element)
