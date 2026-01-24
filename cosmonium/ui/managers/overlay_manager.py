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

"""Overlay manager for managing HUD elements and their anchors."""

import builtins
from itertools import chain
from panda3d.core import TextNode, LVector2

from ..hud.fadetextline import FadeTextLine
from ..skin import UIElement


class OverlayManager:
    """Manages all overlay elements (HUD widgets and docks) and their anchor positions."""

    # Valid anchor positions
    ANCHORS = {'top-left', 'top', 'top-right', 'left', 'center', 'right', 'bottom-left', 'bottom', 'bottom-right'}

    def __init__(self, gui, widgets, docks):
        """Initialize the overlay manager.

        Args:
            gui: The main GUI instance
            widgets: Lists of widgets or None
            docks: List of dock widgets or None
            global_vars: Global variables for widget updates
            skin: UI skin
        """
        self.base = builtins.base
        self.gui = gui
        self.skin = gui.skin
        self.element = UIElement(None, class_='hud', id_='hud')
        self.widgets = {}
        self.shown = True

        # Map anchor names to Panda3D anchor nodes
        self._anchor_map = {
            'top-left': self.base.p2dTopLeft,
            'top': self.base.p2dTopCenter,
            'top-right': self.base.p2dTopRight,
            'left': self.base.p2dLeftCenter,
            'center': self.base.pixel2d,
            'right': self.base.p2dRightCenter,
            'bottom-left': self.base.p2dBottomLeft,
            'bottom': self.base.p2dBottomCenter,
            'bottom-right': self.base.p2dBottomRight,
        }
        if widgets:
            self._initialize_widgets(widgets)
        if docks:
            self._initialize_widgets(docks)
        # Create info widget
        self.info = FadeTextLine('info', 'bottom-left', TextNode.ALeft, LVector2(0, -3), parent=self)
        self.info.set_anchor(self.base.p2dBottomLeft)
        self.info.create()

    def _initialize_widgets(self, widgets):
        """Initialize widget elements."""
        for widget in widgets:
            self.add_widget(widget)

    def _get_anchor(self, anchor_name):
        """Get Panda3D anchor node for the given anchor name.

        Args:
            anchor_name: Name of the anchor position

        Returns:
            Panda3D node for the anchor, or None if invalid
        """
        return self._anchor_map.get(anchor_name)

    def add_widget(self, widget):
        """Add a new widget.

        Args:
            widget: Widget to add
        """
        anchor = self._get_anchor(widget.location)
        if anchor is not None:
            widget.set_parent(self)
            widget.set_anchor(anchor)
            widget.create()

            widgets = self.widgets.setdefault(widget.location, [])
            widgets.append(widget)
        else:
            raise ValueError(f"Invalid anchor name: {widget.location}. Must be one of {self.ANCHORS}")

    def remove_widget(self, widget):
        """Remove a widget from all anchors.

        Args:
            widget: Widget to remove
        """
        for widget_list in self.widgets.values():
            if widget in widget_list:
                widget_list.remove(widget)
                widget.destroy()
                break

    def hide(self):
        """Hide all overlay elements."""
        for widget in chain(*self.widgets.values()):
            widget.hide()
        self.shown = False

    def show(self):
        """Show all overlay elements."""
        for widget in chain(*self.widgets.values()):
            widget.show()
        self.shown = True

    def set_y_offset(self, y_offset):
        """Set vertical offset for top-anchored widgets.

        Args:
            y_offset: Offset to apply
        """
        for anchor_name, widget_list in self.widgets.items():
            if not anchor_name.startswith('top'):
                continue
            offset = y_offset
            for widget in widget_list:
                widget.set_offset((0, offset))
                offset += widget.get_height()

    def update(self, global_vars):
        """Update all overlay elements.

        Args:
            global_vars: Global variables for dynamic updates
        """
        if not self.shown:
            return
        for widget in chain(*self.widgets.values()):
            widget.update(global_vars)

    def update_size(self):
        """Propagate window size update to all overlay elements."""
        for widget in chain(*self.widgets.values()):
            widget.update_size()
