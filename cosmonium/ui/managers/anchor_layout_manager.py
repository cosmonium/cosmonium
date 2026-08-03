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

"""2D anchor node management for the UI.

Creates and positions the named `aspect2d`/`pixel2d` anchor nodes (top-left,
bottom-right, center, ...) that UI widgets attach to, and keeps them in sync
with the window size.
"""

from __future__ import annotations


class AnchorLayout:
    """Manages the `p2d*`/`a2d*` anchor nodes.

    Note: The aspect2d anchors are modified so that aspect2d widget are not scaled when the windows size changes
    This is a hack in contradiction with the Panda3D documentation, but it is the only way to have a consistent UI when
    the window size changes."""

    def __init__(self, base):
        """Create the pixel2d anchor nodes on `base` and attach them under `base.pixel2d`.

        Args:
            base: The ShowBase-derived application object.
        """
        self.base = base
        self.width = 0
        self.height = 0
        self.screen_width = 1
        self.screen_height = 1
        self._create_anchor_nodes()

    def _create_anchor_nodes(self):
        pixel2d = self.base.pixel2d
        self.base.p2dCenter = pixel2d.attach_new_node('p2dCenter')
        self.base.p2dTopCenter = pixel2d.attach_new_node('p2dTopCenter')
        self.base.p2dBottomCenter = pixel2d.attach_new_node('p2dBottomCenter')
        self.base.p2dLeftCenter = pixel2d.attach_new_node('p2dLeftCenter')
        self.base.p2dRightCenter = pixel2d.attach_new_node('p2dRightCenter')

        self.base.p2dTopLeft = pixel2d.attach_new_node('p2dTopLeft')
        self.base.p2dTopRight = pixel2d.attach_new_node('p2dTopRight')
        self.base.p2dBottomLeft = pixel2d.attach_new_node('p2dBottomLeft')
        self.base.p2dBottomRight = pixel2d.attach_new_node('p2dBottomRight')

    def update(self, width, height, screen_width, screen_height):
        """Reposition all anchors for a new window/screen size.

        Args:
            width: New window width, in pixels.
            height: New window height, in pixels.
            screen_width: Physical screen width, in pixels.
            screen_height: Physical screen height, in pixels.

        Returns:
            True if the anchors were recomputed, False if the size was unchanged.
        """
        if self.width == width and self.height == height:
            return False
        self.width = width
        self.height = height
        self.screen_width = screen_width
        self.screen_height = screen_height

        # TODO: This is an ugly hack, should use the proper anchors or define new ones
        arx = 1.0 * screen_width / width
        ary = 1.0 * screen_height / height
        self.base.aspect2d.setScale(arx, 1.0, ary)
        self.base.a2dTop = 1.0 / ary
        self.base.a2dBottom = -1.0 / ary
        self.base.a2dLeft = -1.0 / arx
        self.base.a2dRight = 1.0 / arx
        self.base.a2dTopCenter.setPos(0, 0, self.base.a2dTop)
        self.base.a2dBottomCenter.setPos(0, 0, self.base.a2dBottom)
        self.base.a2dLeftCenter.setPos(self.base.a2dLeft, 0, 0)
        self.base.a2dRightCenter.setPos(self.base.a2dRight, 0, 0)

        self.base.a2dTopLeft.setPos(self.base.a2dLeft, 0, self.base.a2dTop)
        self.base.a2dTopRight.setPos(self.base.a2dRight, 0, self.base.a2dTop)
        self.base.a2dBottomLeft.setPos(self.base.a2dLeft, 0, self.base.a2dBottom)
        self.base.a2dBottomRight.setPos(self.base.a2dRight, 0, self.base.a2dBottom)

        self.base.pixel2d.setScale(2.0 / width, 1.0, 2.0 / height)
        self.base.p2dCenter.setPos(width / 2, 0, -height / 2)
        self.base.p2dTopCenter.setPos(width / 2, 0, 0)
        self.base.p2dBottomCenter.setPos(width / 2, 0, -height)
        self.base.p2dLeftCenter.setPos(0, 0, -height / 2)
        self.base.p2dRightCenter.setPos(width, 0, -height / 2)

        self.base.p2dTopLeft.setPos(0, 0, 0)
        self.base.p2dTopRight.setPos(width - 1, 0, 0)
        self.base.p2dBottomLeft.setPos(0, 0, -height + 1)
        self.base.p2dBottomRight.setPos(width - 1, 0, -height + 1)

        return True
