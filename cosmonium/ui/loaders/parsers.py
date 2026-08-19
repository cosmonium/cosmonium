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

from functools import partial
from typing import Any, Callable, List, Optional, Tuple

from panda3d.core import LColor, LVector4, TextNode

from ..skin import calc_font_size_em, calc_size_em, calc_size_px, calc_size_rem, report_error


class ColorParser:
    """
    Parser for color values.

    Supports:
    - Hex strings: "#RRGGBB"
    - RGB lists: [r, g, b] (values 0-1)
    - RGBA lists: [r, g, b, a] (values 0-1)
    """

    @staticmethod
    def parse(data: Any, context: Optional[str] = None) -> Optional[LColor]:
        """
        Parse a color value from configuration data.

        Args:
            data: Color specification (string or list)
            context: Optional context (e.g. file/entry/selector) for error reporting

        Returns:
            LColor instance or None if parsing fails
        """
        if data is not None:
            if isinstance(data, str):
                if len(data) == 7 and data.startswith('#'):
                    color = LColor(*tuple(int(data[i : i + 2], 16) / 255 for i in (1, 3, 5)), 1.0)
                else:
                    report_error(f"Invalid color {data}", context)
                    color = None
            elif isinstance(data, list):
                if len(data) == 4:
                    color = LColor(*data)
                elif len(data) == 3:
                    color = LColor(*data, 1.0)
                else:
                    report_error(f"Invalid color {data}", context)
                    color = None
        else:
            color = None
        return color


class LengthParser:
    """
    Parser for CSS-like length values.

    Supports:
    - Pixel values: "16px", or a plain number, scaled by the global UI scale factor
    - Em values: "1.5em", relative to the font size of the element the length applies to
      (for `font-size` property, it's relative to the parent element's font size)
    - Rem values: "1.5rem", relative to the skin's root font size
    """

    # Longest suffix first, so "rem" isn't misdetected as "em".
    _UNIT_SUFFIXES = ('rem', 'px', 'em')

    @staticmethod
    def parse(data: Any, context: Optional[str] = None, relative_to_parent: bool = False) -> Optional[Callable]:
        """
        Parse a length value from configuration data.

        Args:
            data: Length specification (string or number)
            context: Optional context (e.g. file/entry/selector) for error reporting
            relative_to_parent: True when parsing the `font-size` property itself, for which "em" is
                relative to the parent element's font size instead of the element's own font size

        Returns:
            Callable returning the length in pixels, or None if parsing fails.
            The callable has the following signature: `length(element, skin)`
        """
        if data is None:
            return None
        if isinstance(data, (int, float)):
            return partial(calc_size_px, float(data))
        if not isinstance(data, str):
            report_error(f"Invalid size {data}", context)
            return None
        unit = next((suffix for suffix in LengthParser._UNIT_SUFFIXES if data.endswith(suffix)), None)
        if unit is None:
            report_error(f"Invalid size {data}", context)
            return None
        try:
            value = float(data[: -len(unit)])
        except ValueError:
            report_error(f"Invalid size {data}", context)
            return None
        if unit == 'px':
            calc = calc_size_px
        elif unit == 'rem':
            calc = calc_size_rem
        elif relative_to_parent:
            calc = calc_font_size_em
        else:
            calc = calc_size_em
        return partial(calc, value)

    @classmethod
    def parse_edge_lengths(cls, data: Any, context: Optional[str] = None) -> Optional[List[Optional[Callable]]]:
        """
        Parse edge lengths (margin, padding) from configuration data.

        Supports CSS-style shorthand:
        - "10px" -> all edges
        - "10px 20px" -> vertical horizontal
        - "10px 20px 30px" -> top horizontal bottom
        - "10px 20px 30px 40px" -> top right bottom left

        Args:
            data: Length specification string or None
            context: Optional context (e.g. file/entry/selector) for error reporting

        Returns:
            List of 4 callables [left, right, bottom, top] in DirectGUI order, or None
        """
        if data is None:
            return None
        if isinstance(data, str):
            items = data.split(' ')
        lengths = [cls.parse(item, context) for item in items]
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
    def parse(
        value: Any, default: Optional[Tuple[str, str]] = None, context: Optional[str] = None
    ) -> Optional[Tuple[str, str]]:
        """
        Parse alignment specification from configuration data.

        Args:
            value: Alignment specification [horizontal, vertical]
            default: Default alignment if value is None..
            context: Optional context (e.g. file/entry/selector) for error reporting

        Returns:
            Tuple of alignment strings ('min', 'max', 'center'), or the default when unspecified

        Note: Returning None means the container uses the alignment matching its direction.
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
            report_error(f"Invalid alignments {value}", context)
            return default


class BorderParser:
    """
    Parser for border values.

    Converts border specifications to LVector4 values.
    """

    @staticmethod
    def parse(value: Any, context: Optional[str] = None) -> Optional[LVector4]:
        """
        Parse border specification from configuration data.

        Args:
            value: Border specification (list of 4 values or single value)
            context: Optional context (e.g. file/entry/selector) for error reporting

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
            report_error(f"Invalid borders {value}", context)
            return None


class GapParser:
    """
    Parser for gap/spacing values.

    Converts gap specifications to tuples.
    """

    @staticmethod
    def parse(value: Any, default: Tuple[int, int] = (0, 0), context: Optional[str] = None) -> Tuple[int, int]:
        """
        Parse gap specification from configuration data.

        Args:
            value: Gap specification (list of 2 values or single value)
            default: Default gap if value is None
            context: Optional context (e.g. file/entry/selector) for error reporting

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
            report_error(f"Invalid gaps {value}", context)
            return default


class TextAlignmentParser:
    """
    Parser for text alignment values.

    Converts text alignment names to TextNode constants.
    """

    @staticmethod
    def parse(value: Any, default: int = TextNode.A_boxed_left, context: Optional[str] = None) -> int:
        """
        Parse text alignment specification from configuration data.

        Args:
            value: Alignment name ("left", "center", "right")
            default: Default alignment if value is None
            context: Optional context (e.g. file/entry/selector) for error reporting

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
            report_error(f"Invalid text align {value}", context)
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
