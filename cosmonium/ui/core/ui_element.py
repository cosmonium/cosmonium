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

"""Base classes for all UI elements in Cosmonium."""

from abc import ABC, abstractmethod


class UIElement(ABC):
    """Abstract base class for all UI elements.

    Provides common interface and properties for windows, HUD widgets, and dock elements.
    """

    def __init__(self, id_, owner=None):
        """Initialize a UI element.

        Args:
            id_: Unique identifier for this element
            owner: Parent UI object that owns this element
        """
        self.id_ = id_
        self.owner = owner
        self.anchor = None
        self.visible = True
        self.instance = None
        if owner is not None:
            self.skin = owner.skin
        else:
            self.skin = None

    def set_owner(self, owner):
        """Set the owner of this element."""
        self.owner = owner
        if owner is not None:
            self.skin = owner.skin
        else:
            self.skin = None

    def set_anchor(self, anchor):
        """Set the anchor point for positioning."""
        self.anchor = anchor
        if self.instance is not None:
            self.instance.reparent_to(self.anchor)

    @abstractmethod
    def create(self):
        """Create the UI element instance."""
        pass

    def show(self):
        """Show the UI element."""
        if self.instance is not None:
            self.instance.unstash()
        self.visible = True

    def hide(self):
        """Hide the UI element."""
        if self.instance is not None:
            self.instance.stash()
        self.visible = False

    def destroy(self):
        """Destroy the UI element and clean up resources."""
        if self.instance is not None:
            self.instance.destroy()
        self.instance = None

    def update(self, global_vars=None):
        """Update the UI element state.

        Args:
            global_vars: Optional global variables for dynamic updates
        """
        pass

    @abstractmethod
    def update_instance(self):
        """Update the visual instance (position, size, etc.)."""
        pass


class PositionedUIElement(UIElement):
    """UI element with position management."""

    def __init__(self, id_, owner=None):
        """Initialize a positioned UI element."""
        super().__init__(id_, owner)
        self.last_pos = None


class FloatingUIElement(PositionedUIElement):
    """UI element for floating elements."""


class OverlayUIElement(UIElement):
    """UI element for non-interactive HUD overlays."""

    def update_size(self):
        """window size update notification."""
        pass


class DockedUIElement(OverlayUIElement):
    """UI element for dock widgets at screen edges."""

    def __init__(self, id_, location, owner=None):
        """Initialize a docked UI element.

        Args:
            id_: Unique identifier
            location: Location of element
            owner: Parent UI object
        """
        super().__init__(id_, owner)
        self.location = location
        self.direction = None
        self.center = location in ('top', 'bottom', 'left', 'right')
        self.offset = (0, 0)
        self.pos = None

    def set_offset(self, offset):
        """Set the offset from the anchor point."""
        self.offset = offset
        self.update_instance()

    def get_height(self):
        """Get the height of the overlay element."""
        return 0

    def get_width(self):
        """Get the width of the overlay element."""
        return 0
