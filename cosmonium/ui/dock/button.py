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
from typing import TYPE_CHECKING

from direct.gui.DirectButton import DirectButton
from direct.gui.DirectGuiBase import DirectGuiWidget
from panda3d.core import LVector3, NodePath, TextNode

from .base import DGuiDockWidget

if TYPE_CHECKING:
    from .dock import Dock


class ButtonDockWidget(DGuiDockWidget):
    """A dock widget showing a clickable button, labelled with a text or with a single icon glyph."""

    element_type = 'button'

    def __init__(
        self,
        text: str,
        event: str,
        menu: str = None,
        is_icon: bool = False,
        rescale: bool = False,
        text_checked: str = None,
        checked=None,
        **kwargs,
    ):
        """
        Args:
            text: The label of the button, or the icon glyph for an icon button
            event: The event sent when the button is clicked
            menu: The name of the popup menu opened when the button is clicked, instead of an event
            is_icon: True when the label is a single icon glyph
            rescale: True to resize the button to fit its content
            kwargs: The layout parameters common to every dock widget, see `DockWidgetBase`
        """
        DGuiDockWidget.__init__(self, **kwargs)
        self.text = text
        self.event = event
        self.menu = menu
        self.is_icon = is_icon
        self.rescale = rescale
        # Optional toggle-button behaviour activated when checked_condition is not None.
        # When it evaluates to true, the button displays the text_checked label instead of text and applies
        # the skin's `checked` pseudo-class.
        self.checked_condition = checked
        self.text_checked = text_checked
        self.button_element = None
        self.skin = None
        self.is_checked = False

    def _open_menu(self):
        builtins.base.gui.open_named_menu(self.menu)

    def create(self, dock: Dock, parent, messenger, skin) -> DirectGuiWidget:
        self.skin = skin
        style = skin.get(self.element)
        font_size = style.resolved_font_size(self.element, skin)
        if self.is_icon:
            # Icon buttons: width and height define the box the glyph must fill, which may differ from the skin's
            # font-size. Scaling the whole node by width / font_size stretches the glyph to exactly fill that box.
            width, height = style.resolved_size(self.element, skin)
            scale = LVector3(width / font_size, 1, height / font_size)
        else:
            scale = LVector3(1, 1, 1)
        if self.menu is not None:
            command = self._open_menu
            extra_args = []
        else:
            command = messenger.send
            extra_args = [self.event]
        button_style = skin.get_style(self.element)
        # The glyph or label is centered in the button unless the skin says otherwise
        button_style.setdefault('text_align', TextNode.A_boxed_center)
        button_kwargs = dict(
            **button_style,
            relief=None,
            pressEffect=1,
            text=self.text,
            textMayChange=True,
            scale=scale,
            command=command,
            extraArgs=extra_args,
        )
        if self.is_icon:
            # A single-glyph icon button. Without an explicit frameSize, DirectButton auto-fits the frame to that
            # glyph's own tight bounds, which varies per icon,-so a row of icon buttons ends up unevenly aligned.
            # We force a uniform square frame instead and _center_icon() below then centers the glyph in it.
            button_kwargs['frameSize'] = (0, font_size, -font_size, 0)
        button = DirectButton(**button_kwargs)
        if self.is_icon:
            self._center_icon(button, font_size)
        bounds = button.getBounds()
        if self.rescale and bounds is not None:
            glyph_width = bounds[1] - bounds[0]
            glyph_height = bounds[3] - bounds[2]
            max_size = max(glyph_width, glyph_height)
            # Shrink the button so the glyph's largest dimension matches the requested size.
            ratio = font_size / max_size
            button.set_scale(LVector3(scale[0] * ratio, 1, scale[2] * ratio))
        return button

    def _center_icon(self, button, font_size):
        """Center an icon glyph within the button frame.

        TextNode has no vertical-centering concept, so a glyph is always placed with its baseline at the frame local
        origin. Different icons have different bounds, the offset needed varies per glyph.

        Correcting DirectGui 'text_pos' property by the measured error does not fully fix the issue, so we apply the
        fix via the plain NodePath transform instead.
        That correction has to be measured and applied relative to stateNodePath[0], not the button itself.

        All four button states (ready/press/rollover/disabled) render the same glyph in the same place, so one
        measurement (state 0) is enough to correct all of them.
        """
        reference = button.stateNodePath[0]
        text_node = button.component('text0')
        bounds = text_node.getTightBounds(reference)
        if bounds is None:
            return
        lo, hi = bounds
        glyph_center_x = (lo[0] + hi[0]) / 2
        glyph_center_z = (lo[2] + hi[2]) / 2
        frame_center_x = font_size / 2
        frame_center_z = -font_size / 2
        delta_x = frame_center_x - glyph_center_x
        delta_z = frame_center_z - glyph_center_z
        for component_name in button.components():
            if not component_name.startswith('text'):
                continue
            component = button.component(component_name)
            pos = NodePath.getPos(component, reference)
            NodePath.setPos(component, reference, pos[0] + delta_x, pos[1], pos[2] + delta_z)

    def update(self, global_vars):
        has_changed = DGuiDockWidget.update(self, global_vars)
        if self.checked_condition is None:
            return has_changed
        checked = bool(self.checked_condition.execute(global_vars))
        if checked == self.is_checked:
            return has_changed
        # Checked state has changed, update the button's style and text accordingly.
        self.is_checked = checked
        new_state = 'checked' if checked else None
        style = self.skin.get_style(self.element, state=new_state)
        button = self.widget.dgui_obj
        for key, value in style.items():
            button[key] = value
        if self.text_checked is not None:
            button['text'] = self.text_checked if checked else self.text
            if self.is_icon:
                style = self.skin.get(self.element, state=new_state)
                font_size = style.resolved_font_size(self.element, self.skin)
                self._center_icon(button, font_size)
        return has_changed
