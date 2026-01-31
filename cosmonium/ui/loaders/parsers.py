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


"""
Parser utilities for UI configuration loading.

This module provides dedicated parser classes for common UI configuration
values like colors, lengths, alignments, borders, and gaps. Each parser
encapsulates the logic for parsing a specific type of value.
"""

from typing import Any, Callable, List, Optional, Tuple

from panda3d.core import LColor, LVector4, TextNode


class ColorParser:
    """
    Parser for color values.

    Supports:
    - Hex strings: "#RRGGBB"
    - RGB lists: [r, g, b] (values 0-1)
    - RGBA lists: [r, g, b, a] (values 0-1)
    """

    @staticmethod
    def parse(data: Any) -> Optional[LColor]:
        """
        Parse a color value from configuration data.

        Args:
            data: Color specification (string or list)

        Returns:
            LColor instance or None if parsing fails
        """
        if data is not None:
            if isinstance(data, str):
                if len(data) == 7 and data.startswith('#'):
                    color = LColor(*tuple(int(data[i : i + 2], 16) / 255 for i in (1, 3, 5)), 1.0)
                else:
                    print(f"Invalid color {data}")
                    color = None
            elif isinstance(data, list):
                if len(data) == 4:
                    color = LColor(*data)
                elif len(data) == 3:
                    color = LColor(*data, 1.0)
                else:
                    print(f"Invalid color {data}")
                    color = None
        else:
            color = None
        return color


class LengthParser:
    """
    Parser for length values with unit support.

    Supports:
    - Pixel values: "16px" or numeric values
    - Em values: "1.5em" (relative to font size)
    """

    @staticmethod
    def parse(data: Any, entry: Any) -> Optional[Callable]:
        """
        Parse a length value from configuration data.

        Args:
            data: Length specification (string or number)
            entry: UI skin entry for calculating sizes

        Returns:
            Callable that calculates the actual size, or None if parsing fails
        """
        if data is not None:
            if isinstance(data, str):
                if len(data) >= 3:
                    value = float(data[0:-2])
                    unit = data[-2:]
                if unit == 'px':
                    size = lambda element, font_size, skin: entry.calc_size_px(  # noqa: E731
                        value, element, font_size, skin
                    )
                elif unit == 'em':
                    size = lambda element, font_size, skin: entry.calc_size_em(  # noqa: E731
                        value, element, font_size, skin
                    )
                else:
                    print(f"Invalid size {data}")
                    size = None
            elif isinstance(data, (int, float)):
                size = lambda element, font_size, skin: entry.calc_size_px(  # noqa: E731
                    data, element, font_size, skin
                )
            else:
                print(f"Invalid size {data}")
                size = None
        else:
            size = None
        return size

    @classmethod
    def parse_edge_lengths(cls, data: Any, entry: Any) -> Optional[List[Optional[Callable]]]:
        """
        Parse edge lengths (margin, padding) from configuration data.

        Supports CSS-style shorthand:
        - "10px" -> all edges
        - "10px 20px" -> vertical horizontal
        - "10px 20px 30px" -> top horizontal bottom
        - "10px 20px 30px 40px" -> top right bottom left

        Args:
            data: Length specification string or None
            entry: UI skin entry for calculating sizes

        Returns:
            List of 4 callables [left, right, bottom, top] in DirectGUI order, or None
        """
        if data is None:
            return None
        if isinstance(data, str):
            items = data.split(' ')
        lengths = [cls.parse(item, entry) for item in items]
        # DirectGUI order is: l, r, b, t
        if len(lengths) == 1:
            lengths = lengths * 4
        elif len(lengths) == 2:
            lengths = [lengths[1], lengths[1], lengths[0], lengths[0]]
        elif len(lengths) == 3:
            lengths = [lengths[1], lengths[1], lengths[2], lengths[0]]
        else:
            lengths = [lengths[3], lengths[1], lengths[2], lengths[0]]
        return lengths


class AlignmentParser:
    """
    Parser for widget alignment values.

    Converts alignment names to DirectGUI alignment values.
    """

    @staticmethod
    def parse(value: Any, default: Tuple[str, str] = ('min', 'min')) -> Tuple[str, str]:
        """
        Parse alignment specification from configuration data.

        Args:
            value: Alignment specification [horizontal, vertical]
            default: Default alignment if value is None

        Returns:
            Tuple of alignment strings ('min', 'max', 'center')
        """
        if isinstance(value, list) and len(value) == 2:
            if value[0] == "left":
                value[0] = "min"
            elif value[0] == "right":
                value[0] = "max"
            if value[1] == "top":
                value[1] = "min"
            elif value[1] == "bottom":
                value[1] = "max"
            return value
        elif value is None:
            return default
        else:
            print(f"Invalid alignments {value}")
            return default


class BorderParser:
    """
    Parser for border values.

    Converts border specifications to LVector4 values.
    """

    @staticmethod
    def parse(value: Any) -> Optional[LVector4]:
        """
        Parse border specification from configuration data.

        Args:
            value: Border specification (list of 4 values or single value)

        Returns:
            LVector4 instance or None
        """
        if isinstance(value, list) and len(value) == 4:
            return LVector4(*value)
        elif isinstance(value, int):
            return LVector4(value)
        elif value is None:
            return None
        else:
            print(f"Invalid borders {value}")
            return None


class GapParser:
    """
    Parser for gap/spacing values.

    Converts gap specifications to tuples.
    """

    @staticmethod
    def parse(value: Any, default: Tuple[int, int] = (0, 0)) -> Tuple[int, int]:
        """
        Parse gap specification from configuration data.

        Args:
            value: Gap specification (list of 2 values or single value)
            default: Default gap if value is None

        Returns:
            Tuple of (horizontal_gap, vertical_gap)
        """
        if isinstance(value, list) and len(value) == 2:
            return tuple(value)
        elif isinstance(value, int):
            return (value, value)
        elif value is None:
            return default
        else:
            print(f"Invalid gaps {value}")
            return default


class TextAlignmentParser:
    """
    Parser for text alignment values.

    Converts text alignment names to TextNode constants.
    """

    @staticmethod
    def parse(value: Any, default: int = TextNode.A_boxed_left) -> int:
        """
        Parse text alignment specification from configuration data.

        Args:
            value: Alignment name ("left", "center", "right")
            default: Default alignment if value is None

        Returns:
            TextNode alignment constant
        """
        if value == "left":
            return TextNode.A_boxed_left
        elif value == "center":
            return TextNode.A_boxed_center
        elif value == "right":
            return TextNode.A_boxed_right
        elif value is None:
            return default
        else:
            print(f"Invalid text align {value}")
            return default


class ParsersCollection:
    """
    Collection of all parser instances for convenient access.

    This class provides a single interface to access all parsers,
    making it easy to pass parsing capabilities to widget loaders.
    """

    _instance = None

    def __init__(self) -> None:
        """Initialize all parser instances."""
        self.color = ColorParser()
        self.length = LengthParser()
        self.alignment = AlignmentParser()
        self.border = BorderParser()
        self.gap = GapParser()
        self.text_alignment = TextAlignmentParser()

    @classmethod
    def get_instance(cls) -> 'ParsersCollection':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
