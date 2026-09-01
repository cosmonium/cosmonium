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

This module provides dedicated parser classes for the values shared by the skin and the widget
configurations: colors, CSS-like lengths, widget alignments and text alignments.
Each parser encapsulates the logic for parsing a specific type of value.
"""

from __future__ import annotations

from functools import partial
from typing import Any, Callable, List, Optional, Tuple

from panda3d.core import LColor, TextNode

from ..skin import ALIGNMENT_VALUES, calc_font_size_em, calc_size_em, calc_size_px, calc_size_rem, report_error


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

    Note: A length can only be turned into a pixel value once the element it applies to and the skin
    resolving its style are known, so parsing returns a callable evaluated at widget creation time.
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
        if isinstance(data, bool):
            # If not tested explicitly, a boolean is accepted as a number.
            report_error(f"Invalid size {data}", context)
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
    def parse_values(cls, data: Any, count: int, context: Optional[str] = None) -> Optional[List[Optional[Callable]]]:
        """
        Parse a CSS-like shorthand made of one to `count` lengths.

        Args:
            data: A single length, or several of them separated by spaces, or a list of lengths
            count: Maximum number of lengths accepted
            context: Optional context (e.g. file/entry/selector) for error reporting

        Returns:
            The list of parsed lengths, or None if unset or invalid
        """
        if data is None:
            return None
        if isinstance(data, str):
            items = data.split()
        elif isinstance(data, (list, tuple)):
            items = list(data)
        else:
            items = [data]
        if not items or len(items) > count:
            report_error(f"Invalid value {data}, expected 1 to {count} lengths", context)
            return None
        return [cls.parse(item, context) for item in items]

    @classmethod
    def parse_edge_lengths(cls, data: Any, context: Optional[str] = None) -> Optional[List[Optional[Callable]]]:
        """
        Parse the edge lengths of a box from configuration data.

        Supports the CSS shorthand:
        - "10px" -> all edges
        - "10px 20px" -> vertical horizontal
        - "10px 20px 30px" -> top horizontal bottom
        - "10px 20px 30px 40px" -> top right bottom left

        Args:
            data: Length specification, or None
            context: Optional context (e.g. file/entry/selector) for error reporting

        Returns:
            List of 4 lengths [left, right, bottom, top] in DirectGUI order, or None
        """
        lengths = cls.parse_values(data, 4, context)
        if lengths is None:
            return None
        # DirectGUI order is: l, r, b, t
        if len(lengths) == 1:
            return lengths * 4
        if len(lengths) == 2:
            return [lengths[1], lengths[1], lengths[0], lengths[0]]
        if len(lengths) == 3:
            return [lengths[1], lengths[1], lengths[2], lengths[0]]
        return [lengths[3], lengths[1], lengths[2], lengths[0]]

    @classmethod
    def parse_gap(cls, data: Any, context: Optional[str] = None) -> Optional[Tuple[Optional[Callable], ...]]:
        """
        Parse a `gap`, the spacing between the children of a container.

        Follows the CSS shorthand, "<row-gap> <column-gap>", a single value setting both.

        Args:
            data: Gap specification, or None
            context: Optional context (e.g. file/entry/selector) for error reporting

        Returns:
            The (column, row) gaps, in the order expected by the sizer, or None
        """
        lengths = cls.parse_values(data, 2, context)
        if lengths is None:
            return None
        if len(lengths) == 1:
            return (lengths[0], lengths[0])
        return (lengths[1], lengths[0])


class AlignmentParser:
    """
    Parser for the alignment of a widget inside the cell it occupies in its parent's layout.

    Follows the CSS `align-self` / `justify-self` keywords: `start`, `end`, `center` and `stretch`,
    plus the directional aliases `left`/`right` (horizontal) and `top`/`bottom` (vertical).
    """

    @staticmethod
    def parse(value: Any, default: Optional[str] = None, context: Optional[str] = None) -> Optional[str]:
        """
        Parse an alignment keyword from configuration data.

        Args:
            value: Alignment keyword, or None
            default: Value to return when the alignment is unset or invalid
            context: Optional context (e.g. file/entry/selector) for error reporting

        Returns:
            The alignment value expected by the sizer ('min', 'max', 'center' or 'expand')

        Note: Returning None means the widget uses the default alignment of the layout holding it.
        """
        if value is None:
            return default
        alignment = ALIGNMENT_VALUES.get(value)
        if alignment is None:
            report_error(f"Invalid alignment {value}", context)
            return default
        return alignment


class TextAlignmentParser:
    """
    Parser for the alignment of the text inside a widget.
    """

    _ALIGNMENTS = {
        'left': TextNode.A_boxed_left,
        'center': TextNode.A_boxed_center,
        'right': TextNode.A_boxed_right,
    }

    @classmethod
    def parse(cls, value: Any, default: Optional[int] = None, context: Optional[str] = None) -> Optional[int]:
        """
        Parse a text alignment specification from configuration data.

        Args:
            value: Alignment name ("left", "center" or "right"), or None
            default: Value to return when the alignment is unset or invalid
            context: Optional context (e.g. file/entry/selector) for error reporting

        Returns:
            TextNode alignment constant
        """
        if value is None:
            return default
        alignment = cls._ALIGNMENTS.get(value)
        if alignment is None:
            report_error(f"Invalid text align {value}", context)
            return default
        return alignment


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
        self.text_alignment = TextAlignmentParser()

    @classmethod
    def get_instance(cls) -> ParsersCollection:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
