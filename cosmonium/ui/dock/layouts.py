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

from typing import TYPE_CHECKING

from directguilayout.gui import Sizer

from ..skin import UIElement, UISkin, combine_classes, resolve_length
from .base import DockWidgetBase
from .decorated_sizer import DecoratedSizer

if TYPE_CHECKING:
    from .dock import Dock


class SpaceDockWidget(DockWidgetBase):
    """Empty space reserved in a layout.

    A spacer has no visual of its own; it only takes room.
    """

    element_type = 'spacer'

    def __init__(self, width=None, height=None, **kwargs):
        """
        Args:
            width: Width of the space to reserve, overriding the skin, or None
            height: Height of the space to reserve, overriding the skin, or None
            kwargs: The layout parameters common to every dock widget, see `DockWidgetBase`
        """
        DockWidgetBase.__init__(self, **kwargs)
        self.width = width
        self.height = height

    def build(self, dock: Dock, parent, skin: UISkin) -> None:
        self.create_element(parent)
        style = skin.get(self.element)
        # A spacer has no content to be sized by, an unset dimension simply reserves nothing.
        width, height = style.resolved_size(self.element, skin, default=0)
        if self.width is not None:
            width = resolve_length(self.width, self.element, skin)
        if self.height is not None:
            height = resolve_length(self.height, self.element, skin)
        # A sizer takes a plain tuple as an empty cell of the given size.
        self.widget = (width, height)


class LayoutDockWidget(DockWidgetBase):
    """A container laying out its children in a row or in a column.

    The container is drawn as a frame, styled by the skin, and its children are laid out inside the
    content area of that frame.
    """

    element_type = 'frame'

    def __init__(
        self,
        direction: str,
        widgets: list[DockWidgetBase],
        gap=None,
        padding=None,
        element_class: str = 'layout',
        **kwargs,
    ):
        """
        Args:
            direction: Direction in which the children are laid out, horizontal or vertical
            widgets: The children of this layout
            gap: Space between the children, overriding the skin, or None
            padding: Edge lengths of the padding, overriding the skin, or None
            element_class: Structural class of the skin element of this layout
            kwargs: The layout parameters common to every dock widget, see `DockWidgetBase`
        """
        DockWidgetBase.__init__(self, **kwargs)
        self.direction = direction
        self.element = UIElement(self.element_type, class_=combine_classes(element_class, self.class_), id_=self.id_)
        self.widget = DecoratedSizer(self.element, direction, gap=gap, padding=padding)
        self.widgets = widgets
        self.instance = None

    @property
    def sizer(self) -> DecoratedSizer:
        """The sizer holding the whole layout, border box included."""
        return self.widget

    @property
    def content_sizer(self) -> Sizer:
        """The sizer the children of this layout are added to."""
        return self.widget.content

    def default_alignments(self) -> tuple[str, str]:
        """Default alignment of the children that do not request one.

        Children are packed from the start of the layout direction and centered across it.
        """
        if self.direction == 'horizontal':
            return ('min', 'center')
        else:
            return ('center', 'min')

    def build(self, dock: Dock, parent, skin: UISkin) -> None:
        self.create_element(parent)
        self.widget.create(dock, parent, skin)
        self.instance = parent.instance
        for widget in self.widgets:
            widget.add_to(dock, self, skin)

    def update_layout(self):
        min_size = self.sizer.update_min_size()
        self.sizer.update(min_size)

    def update(self, global_vars):
        has_changed = False
        for widget in self.widgets:
            has_changed = widget.update(global_vars) or has_changed
        if has_changed:
            self.update_layout()
        return has_changed
