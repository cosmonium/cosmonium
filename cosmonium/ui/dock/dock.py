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

from direct.gui.DirectFrame import DirectFrame
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import LVector3

from ... import settings
from ..core.ui_element import DockedUIElement
from ..skin import UIElement, combine_classes


class Dock(DockedUIElement):

    def __init__(self, id_, direction, location, layout, parent=None):
        DockedUIElement.__init__(self, id_, location, parent=parent)
        self.direction = direction
        self.layout = layout
        self.anchor = None
        self.element = None
        self.pos = LVector3(0)
        # The screen edge this dock hides into: 'top', 'bottom', 'left' or 'right'.
        if direction == "horizontal":
            self.edge = 'top' if location.startswith('top') else 'bottom'
        else:
            self.edge = 'left' if location.endswith('left') else 'right'
        # Auto-hide: the dock slides out of view when the mouse is not over it,
        # and slides back in when the mouse lingers near that edge of the window.
        self.auto_hide = False
        self._mouse_pixel = None
        self._near_edge = False
        # `pins` lets widgets that pop content outside the dock bounds force it to stay visible
        # for as long as that pop-up is open.
        # Multiple widgets may pin the dock at the same time..
        self.pins = set()
        self.slide = 0.0  # 0 = fully shown, 1 = fully slid out of view
        self.leave_timer = 0.0
        self.reveal_timer = 0.0

    def create(self):
        self.element = UIElement('frame', class_=combine_classes('dock', self.layout.element.class_), id_=self.id_)
        self.instance = DirectFrame(parent=self.anchor, **self.skin.get_style(self.element))
        # The dock is the root of the layout tree: its layout is built, but not placed in a parent.
        self.layout.build(self, self, self.skin)
        # Call update_size() to update the dock size and position it correctly relative to its configured location.
        self.update_size()

    def pin(self, key):
        """Force the dock to stay visible on behalf of the given widget."""
        self.pins.add(key)

    def unpin(self, key):
        """Release a previous `pin` for the given widget.
        If that key isn't currently pinning the dock, the request is ignored."""
        self.pins.discard(key)

    def set_auto_hide(self, enabled):
        self.auto_hide = enabled
        if not enabled:
            self.slide = 0.0
            self.leave_timer = 0.0
            self.reveal_timer = 0.0
            self.update_instance()

    def set_mouse_state(self, mouse_pixel, near_edge):
        """Refresh the shared per-frame mouse state used to trigger auto-hide.

        Args:
            mouse_pixel: (x, y) mouse position in window pixels, or None if the mouse isn't over the window
            near_edge: True if the mouse is close enough to the window edge to reveal the dock
        """
        self._mouse_pixel = mouse_pixel
        self._near_edge = near_edge

    def _hide_vector(self):
        """Unit vector, in the dock coordinate space, pointing off-screen past the edge."""
        return {
            'top': LVector3(0, 0, 1),
            'bottom': LVector3(0, 0, -1),
            'left': LVector3(-1, 0, 0),
            'right': LVector3(1, 0, 0),
        }[self.edge]

    def _hide_distance(self):
        """Distance, in pixels, the dock must travel to be fully hidden past its edge."""
        # A small margin on top of the dock's own thickness so no extra (border, shadow) remains visible.
        margin = 4
        if self.direction == "horizontal":
            return self.get_height() + margin
        else:
            return self.get_width() + margin

    def _current_rect(self):
        """The dock's current on-screen rectangle in window pixel coordinates."""
        width, height = self.get_size()
        pos = self.pos + LVector3(self.offset[0], 0, self.offset[1])
        if self.auto_hide and self.slide:
            pos = pos + self._hide_vector() * (self._hide_distance() * self.slide)
        anchor_pos = self.anchor.get_pos(builtins.base.pixel2d)
        left = anchor_pos[0] + pos[0]
        right = left + width
        top = -(anchor_pos[2] + pos[2])
        bottom = top + height
        return left, right, top, bottom

    def _mouse_within_rect(self):
        if self._mouse_pixel is None:
            return False
        x, y = self._mouse_pixel
        left, right, top, bottom = self._current_rect()
        return left <= x <= right and top <= y <= bottom

    def update_instance(self):
        if self.instance is None:
            return
        pos = self.pos + LVector3(self.offset[0], 0, self.offset[1])
        if self.auto_hide and self.slide:
            pos = pos + self._hide_vector() * (self._hide_distance() * self.slide)
        self.instance.set_pos(pos)

    def get_size(self):
        """The dock outer size."""
        return self.layout.sizer.get_size()

    def get_width(self):
        return self.get_size()[0]

    def get_height(self):
        return self.get_size()[1]

    def update_size(self):
        self.layout.update_layout()
        size = self.get_size()
        if self.direction == "horizontal":
            if self.center:
                self.pos[0] = -size[0] / 2
            elif self.location.endswith("left"):
                self.pos[0] = 0
            elif self.location.endswith("right"):
                self.pos[0] = -size[0] - 1
            if self.location.startswith("top"):
                self.pos[2] = -self.offset[1]
            elif self.location.startswith("bottom"):
                self.pos[2] = size[1] + 1
        else:
            if self.location.endswith("left"):
                self.pos[0] = 0
            elif self.location.endswith("right"):
                self.pos[0] = -size[0] - 1
            if self.center:
                self.pos[2] = size[1] / 2
            elif self.location.startswith("top"):
                self.pos[2] = -self.offset[1]
            elif self.location.startswith("bottom"):
                self.pos[2] = size[1] + 1
        self.update_instance()

    def _update_auto_hide(self):
        dt = globalClock.getDt()
        wants_open = self._mouse_within_rect() or bool(self.pins)
        # Target it 1.0 if the dock should be fully hidden, or 0.0 if it should be fully shown.
        # (following self.slide state))
        if wants_open:
            self.leave_timer = 0.0
            target = 0.0
        else:
            self.leave_timer += dt
            target = 1.0 if self.leave_timer >= settings.dock_auto_hide_delay else 0.0
        if target == 1.0 and self._near_edge:
            if self.slide < 1.0:
                # The dock hasn't fully slid out of view yet: cancel the hide immediately.
                target = 0.0
                self.leave_timer = 0.0
                self.reveal_timer = 0.0
            else:
                # The dock is already fully hidden: require the mouse to hover at the edge for
                # a while before triggering the reveal.
                self.reveal_timer += dt
                if self.reveal_timer >= settings.dock_reveal_delay:
                    target = 0.0
                    self.leave_timer = 0.0
        else:
            self.reveal_timer = 0.0
        duration = max(settings.dock_slide_duration, 1e-3)
        step = dt / duration
        if self.slide < target:
            self.slide = min(target, self.slide + step)
        elif self.slide > target:
            self.slide = max(target, self.slide - step)
        else:
            return
        self.update_instance()

    def update(self, global_vars):
        if self.layout.update(global_vars):
            # Call update_size() to update the dock size and position it correctly relative to its configured location.
            self.update_size()
        if self.auto_hide:
            self._update_auto_hide()
