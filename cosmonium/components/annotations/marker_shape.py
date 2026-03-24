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


from enum import IntEnum


class MarkerShape(IntEnum):
    """Enumeration of available marker shapes.

    Attributes:
        DIAMOND: Diamond shape.
        PLUS: Plus/cross shape.
        SQUARE: Square outline.
        TRIANGLE: Triangle shape.
        X: X shape.
        FILLEDSQUARE: Filled square.
        LEFTARROW: Left-pointing arrow.
        RIGHTARROW: Right-pointing arrow.
        UPARROW: Up-pointing arrow.
        DOWNARROW: Down-pointing arrow.
        CIRCLE: Circle outline.
        DISK: Filled circle/disk.
    """

    DIAMOND = 0
    PLUS = 1
    SQUARE = 2
    TRIANGLE = 3
    X = 4
    FILLEDSQUARE = 5
    LEFTARROW = 6
    RIGHTARROW = 7
    UPARROW = 8
    DOWNARROW = 9
    CIRCLE = 10
    DISK = 11

    @classmethod
    def from_string(cls, name):
        """Get a MarkerShape from its string name.

        Args:
            name: String name of the marker shape (case-insensitive).

        Returns:
            The corresponding MarkerShape enum value, or DIAMOND if not found.
        """
        mapping = {
            'diamond': cls.DIAMOND,
            'plus': cls.PLUS,
            'square': cls.SQUARE,
            'triangle': cls.TRIANGLE,
            'x': cls.X,
            'filledsquare': cls.FILLEDSQUARE,
            'leftarrow': cls.LEFTARROW,
            'rightarrow': cls.RIGHTARROW,
            'uparrow': cls.UPARROW,
            'downarrow': cls.DOWNARROW,
            'circle': cls.CIRCLE,
            'disk': cls.DISK,
        }
        return mapping.get(name.lower(), cls.DIAMOND)
