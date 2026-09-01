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

from __future__ import annotations

import builtins
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectGuiBase import DirectGuiWidget
from directguilayout.gui import Widget as SizerWidget
from panda3d.core import PNMImage, Texture

from ..skin import UIElement, UISkin, combine_classes, resolve_edge_lengths

if TYPE_CHECKING:
    from .dock import Dock
    from .layouts import LayoutDockWidget


class DockWidgetBase(ABC):
    """Base class of every widget that can be placed in a dock layout."""

    # Type of the skin element of this widget
    element_type: str = None
    # Optional class of the skin element
    element_class: str = None

    def __init__(self, align=None, justify=None, margin=None, grow=None, class_=None, id_=None):
        """
        Args:
            align: Vertical alignment in the cell, overriding the skin, or None
            justify: Horizontal alignment in the cell, overriding the skin, or None
            margin: Edge lengths of the margin, overriding the skin, or None
            grow: Share of the leftover space of the parent layout claimed by this widget, or None
            class_: Extra skin class(es) attached to this widget
            id_: Skin id of this widget
        """
        # Sizer wrapper around the DirectGui widget, or a tuple representing a sizer
        self.widget: SizerWidget | tuple = None
        self.element: UIElement = None
        self.align = align
        self.justify = justify
        self.margin = margin
        self.grow = grow
        self.class_ = class_
        self.id_ = id_

    def create_element(self, parent: LayoutDockWidget | Dock) -> UIElement:
        """
        Create the skin element of this widget and attach it to the element of its parent.

        Args:
            parent: The parent element this widget is placed in

        Returns:
            The skin element of this widget
        """
        if self.element is None:
            self.element = UIElement(
                self.element_type, class_=combine_classes(self.element_class, self.class_), id_=self.id_
            )
        self.element.parent = parent.element
        return self.element

    def get_cell_parameters(self, parent: LayoutDockWidget | Dock, skin: UISkin) -> dict:
        """
        Resolve the layout parameters of the cell this widget occupies in its parent layout.

        Each parameter set in the configuration of the widget overrides the one the skin gives it.

        Args:
            parent: The layout this widget is placed in
            skin: The skin of the ui

        Returns:
            The keyword arguments describing the cell.
        """
        style = skin.get(self.element)
        margin = self.margin if self.margin is not None else style.margin
        # A widget that requests no alignment, neither in the skin nor in its configuration, is
        # placed using the default alignment of the layout holding it.
        default_justify, default_align = parent.default_alignments()
        justify = self.justify or style.justify or default_justify
        align = self.align or style.align or default_align
        # `grow` is the share of the leftover space claimed along the direction of the parent
        # layout; the widget never grows in the other direction.
        grow = self.grow if self.grow is not None else 0.0
        proportions = (grow, 0.0) if parent.direction == 'horizontal' else (0.0, grow)
        return {
            'proportions': proportions,
            'alignments': (justify, align),
            'borders': resolve_edge_lengths(margin, self.element, skin),
        }

    @abstractmethod
    def build(self, dock: Dock, parent: LayoutDockWidget | Dock, skin: UISkin) -> None:
        """
        Create the skin element and the layout object of this widget.

        Args:
            dock: The dock this widget belongs to
            parent: The layout, or the dock, this widget is placed in
            skin: The skin of the ui
        """

    def add_to(self, dock: Dock, parent: LayoutDockWidget, skin: UISkin) -> None:
        """
        Create this widget and place it in the parent layout.

        Args:
            dock: The dock this widget belongs to
            parent: The layout this widget is placed in
            skin: The skin of the ui
        """
        self.build(dock, parent, skin)
        # TODO: Should not use the internal content_sizer
        parent.content_sizer.add(self.widget, **self.get_cell_parameters(parent, skin))

    def compile(self):
        pass

    def update(self, global_vars):
        return False


class DGuiDockWidget(DockWidgetBase):
    """Base class of the dock widgets using a DirectGui widget."""

    def __init__(self, enabled=None, **kwargs):
        DockWidgetBase.__init__(self, **kwargs)
        self.enabled_condition = enabled
        self.is_enabled = True

    @abstractmethod
    def create(self, dock: Dock, parent, messenger, skin: UISkin) -> DirectGuiWidget:
        """
        Create the DirectGui widget itself, styled with the skin element of this widget.

        Args:
            dock: The dock this widget belongs to
            parent: The layout this widget is placed in
            messenger: The messenger the widget sends its events to
            skin: The skin of the ui

        Returns:
            The created DirectGui widget
        """

    def build(self, dock: Dock, parent, skin: UISkin) -> None:
        self.create_element(parent)
        instance = self.create(dock, parent, builtins.base.messenger, skin)
        instance.reparent_to(dock.instance)
        self.widget = SizerWidget(instance)

    def update(self, global_vars):
        if self.enabled_condition is None:
            return False
        enabled = bool(self.enabled_condition.execute(global_vars))
        if enabled == self.is_enabled:
            return False
        self.is_enabled = enabled
        self.widget.dgui_obj['state'] = DGG.NORMAL if enabled else DGG.DISABLED
        return False


class FrameColorTexture:

    def __init__(self, background_color, border_color):
        self.size = 3
        self.image = PNMImage(self.size, self.size, num_channels=4)
        for i in range(self.size):
            for j in range(self.size):
                self.image.set_xel_a(j, i, *border_color)
        self.image.set_xel_a(1, 1, *background_color)
        self.texture = Texture()
        self.texture.load(self.image)
