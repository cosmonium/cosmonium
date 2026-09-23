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
from typing import Any, Optional, Tuple

from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectGuiBase import DirectGuiWidget
from direct.gui.DirectLabel import DirectLabel
from panda3d.core import Point3, TextNode

from ..skin import UIElement, UISkin, resolve_edge_lengths
from .decorated_frame import FrameDecoration

# Which side of the anchor widget the tooltip grows towards.
SideLiteral = str  # one of 'above', 'below', 'left', 'right'


class Tooltip:
    """A floating tooltip."""

    def __init__(self):
        self.frame: Optional[DirectFrame] = None
        self.label: Optional[DirectLabel] = None
        self.decoration: Optional[FrameDecoration] = None
        self.padding: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
        self.frame_size: Tuple[float, float] = (0.0, 0.0)
        # Identity of whichever caller currently owns the shown tooltip, or None when hidden
        self.owner: Any = None

    def show(self, owner: Any, text: str, anchor: DirectGuiWidget, side: SideLiteral, skin: UISkin) -> None:
        """
        Show `text` tooltip next to `anchor`, on the given side of it.

        Args:
            owner: Identifies the caller.
            text: The tooltip text.
            anchor: The DirectGui widget the tooltip is shown next to.
            side: Which side of `anchor` to place the tooltip: 'above', 'below', 'left' or 'right'.
            skin: The active skin.
        """
        self.owner = owner
        if self.frame is None:
            self._create(text, skin)
        else:
            self.label['text'] = text
        self._layout()
        self._position(anchor, side)
        self.frame.show()

    def hide(self, owner: Any) -> None:
        """Hide the tooltip, but only if `owner` is the one that last showed it."""
        if self.frame is None or owner is not self.owner:
            return
        self.owner = None
        self.frame.hide()

    def _create(self, text: str, skin: UISkin) -> None:
        frame_element = UIElement('frame', class_='tooltip')
        self.decoration = FrameDecoration(frame_element, skin)
        self.padding = resolve_edge_lengths(skin.get(frame_element).padding, frame_element, skin)
        self.frame = DirectFrame(parent=builtins.base.pixel2d)
        self.frame.hide()

        label_element = UIElement('label', class_='tooltip')
        style = skin.get_style(label_element)
        style.setdefault('text_align', TextNode.A_center)
        # The frame behind it draws the background; a second, square one from the label would
        # clash with (or show through past) the frame's rounded corners.
        style['frameColor'] = (0, 0, 0, 0)
        self.label = DirectLabel(parent=self.frame, text=text, textMayChange=True, **style)

    def _layout(self) -> None:
        """Resize the frame and its background/border/corner geometry to fit the current text."""
        self.label.resetFrameSize()
        label_bounds = self.label.getBounds()
        left, right, bottom, top = self.padding
        inset = self.decoration.content_inset
        left, right, bottom, top = left + inset, right + inset, bottom + inset, top + inset
        label_width = label_bounds[1] - label_bounds[0]
        label_height = label_bounds[3] - label_bounds[2]
        width = label_width + left + right
        height = label_height + bottom + top
        self.frame_size = (width, height)
        self.frame['frameSize'] = (0, width, -height, 0)
        self.frame['frameColor'] = self.decoration.frame_color()
        self.frame['geom'] = self.decoration.build_geom(self.frame_size)
        # Place the label so its own (possibly off-center) glyph bounds land inset from the frame edges.
        self.label.set_pos(left - label_bounds[0], 0, -top - label_bounds[3])

    def _position(self, anchor: DirectGuiWidget, side: SideLiteral) -> None:
        anchor_bounds = anchor.getBounds()
        if anchor_bounds is None:
            return
        left, right, bottom, top = anchor_bounds
        # Convert anchor rectangle to global coordinates to position the tooptip
        to_root = anchor.get_mat(self.frame.get_parent())
        corners = [to_root.xform_point(Point3(x, 0, z)) for x in (left, right) for z in (bottom, top)]
        lo_x, hi_x = min(c[0] for c in corners), max(c[0] for c in corners)
        lo_z, hi_z = min(c[2] for c in corners), max(c[2] for c in corners)
        width, height = self.frame_size
        gap = height * 0.3
        if side == 'left':
            center_x = lo_x - width / 2 - gap
            center_z = (lo_z + hi_z) / 2
        elif side == 'right':
            center_x = hi_x + width / 2 + gap
            center_z = (lo_z + hi_z) / 2
        elif side == 'above':
            center_x = (lo_x + hi_x) / 2
            center_z = hi_z + height / 2 + gap
        else:
            center_x = (lo_x + hi_x) / 2
            center_z = lo_z - height / 2 - gap
        self.frame.set_pos(center_x - width / 2, 0, center_z + height / 2)


# Single shared instance: only one tooltip is ever shown across the whole application.
tooltip_instance = Tooltip()
