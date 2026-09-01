#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2025 Laurent Deru.
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
Unit tests for parser classes.

This module contains comprehensive tests for all parser utilities
used in UI configuration loading.
"""

import pytest
from panda3d.core import TextNode

from cosmonium.ui.loaders.parsers import (
    AlignmentParser,
    ColorParser,
    LengthParser,
    ParsersCollection,
    TextAlignmentParser,
)
from cosmonium.ui.skin import Selector, UIElement, UISkin, UISkinEntry


class TestColorParser:
    """Tests for ColorParser."""

    def test_parse_hex_color(self):
        """Test parsing hex color strings."""
        parser = ColorParser()

        # Red
        color = parser.parse("#FF0000")
        assert color.x == pytest.approx(1.0)
        assert color.y == pytest.approx(0.0)
        assert color.z == pytest.approx(0.0)
        assert color.w == pytest.approx(1.0)

        # Green
        color = parser.parse("#00FF00")
        assert color.x == pytest.approx(0.0)
        assert color.y == pytest.approx(1.0)
        assert color.z == pytest.approx(0.0)

        # Blue
        color = parser.parse("#0000FF")
        assert color.x == pytest.approx(0.0)
        assert color.y == pytest.approx(0.0)
        assert color.z == pytest.approx(1.0)

    def test_parse_rgb_list(self):
        """Test parsing RGB list."""
        parser = ColorParser()
        color = parser.parse([1.0, 0.5, 0.25])
        assert color.x == pytest.approx(1.0)
        assert color.y == pytest.approx(0.5)
        assert color.z == pytest.approx(0.25)
        assert color.w == pytest.approx(1.0)

    def test_parse_rgba_list(self):
        """Test parsing RGBA list."""
        parser = ColorParser()
        color = parser.parse([1.0, 0.5, 0.25, 0.8])
        assert color.x == pytest.approx(1.0)
        assert color.y == pytest.approx(0.5)
        assert color.z == pytest.approx(0.25)
        assert color.w == pytest.approx(0.8)

    def test_parse_none(self):
        """Test parsing None returns None."""
        parser = ColorParser()
        assert parser.parse(None) is None

    def test_parse_invalid_hex(self, caplog):
        """Test parsing invalid hex string."""
        parser = ColorParser()
        color = parser.parse("#XYZ")
        assert color is None
        assert "Invalid color" in caplog.text

    def test_parse_invalid_list(self, caplog):
        """Test parsing invalid list."""
        parser = ColorParser()
        color = parser.parse([1.0, 0.5])  # Too few values
        assert color is None
        assert "Invalid color" in caplog.text


def make_skin(root_font_size=16, **entry_config):
    """Build a skin whose single entry, matching any element, holds the given properties."""
    skin = UISkin()
    skin.root_font_size = root_font_size
    entry = UISkinEntry(Selector(None, None, None, None), {})
    for key, value in entry_config.items():
        setattr(entry, key, value)
    skin.add_entry(entry)
    return skin


class TestLengthParser:
    """Tests for LengthParser."""

    def test_parse_pixels(self):
        """A length in pixels does not depend on any context."""
        length = LengthParser.parse("16px")

        assert length(None, None) == 16

    def test_parse_em(self):
        """A length in em is relative to the font size of the element it applies to."""
        skin = make_skin(font_size=LengthParser.parse("12px"))
        element = UIElement('button')

        length = LengthParser.parse("1.5em")

        assert length(element, skin) == 18

    def test_parse_em_of_font_size_is_relative_to_the_parent(self):
        """For font-size property, em is relative to the parent's font size."""
        skin = make_skin(font_size=LengthParser.parse("12px"))
        element = UIElement('button', parent=UIElement('frame'))

        length = LengthParser.parse("1.5em", relative_to_parent=True)

        assert length(element, skin) == 18

    def test_parse_em_falls_back_to_the_root_font_size(self):
        """An em length applied to an element who has no defined font size, uses the root font size."""
        skin = make_skin(root_font_size=20)

        length = LengthParser.parse("1.5em")

        assert length(UIElement('button'), skin) == 30

    def test_parse_rem(self):
        """Test parsing rem values, relative to the skin's root font size."""
        skin = make_skin(root_font_size=20)

        length = LengthParser.parse("1.5rem")

        assert length(None, skin) == 30

    def test_parse_invalid_string_does_not_crash(self, caplog):
        """A string containing an invalid unit should be reported."""
        assert LengthParser.parse("1x") is None
        assert "Invalid size 1x" in caplog.text

    def test_parse_invalid_number_does_not_crash(self, caplog):
        """A string with a valid unit but an invalid number should be reported."""
        assert LengthParser.parse("abcpx") is None
        assert "Invalid size abcpx" in caplog.text

    def test_parse_numeric(self):
        """A plain number is a number of pixels."""
        assert LengthParser.parse(20)(None, None) == 20
        assert LengthParser.parse(15.5)(None, None) == 15.5

    def test_parse_none(self):
        """Test parsing None returns None."""
        assert LengthParser.parse(None) is None


class TestEdgeLengthsParser:
    """Tests for the parsing of the `margin` and `padding` shorthands."""

    @staticmethod
    def resolve(data):
        lengths = LengthParser.parse_edge_lengths(data)
        return [length(None, None) for length in lengths]

    def test_a_single_length_applies_to_the_four_edges(self):
        assert self.resolve("10px") == [10, 10, 10, 10]

    def test_two_lengths_are_vertical_then_horizontal(self):
        # DirectGUI order: left, right, bottom, top
        assert self.resolve("10px 20px") == [20, 20, 10, 10]

    def test_three_lengths_are_top_horizontal_bottom(self):
        assert self.resolve("10px 20px 30px") == [20, 20, 30, 10]

    def test_four_lengths_are_top_right_bottom_left(self):
        assert self.resolve("10px 20px 30px 40px") == [40, 20, 30, 10]

    def test_a_plain_number_is_accepted(self):
        assert self.resolve(4) == [4, 4, 4, 4]

    def test_parse_none(self):
        """Test parsing None returns None."""
        assert LengthParser.parse_edge_lengths(None) is None

    def test_too_many_lengths_are_reported(self, caplog):
        assert LengthParser.parse_edge_lengths("1px 2px 3px 4px 5px") is None
        assert "expected 1 to 4 lengths" in caplog.text


class TestGapParser:
    """Tests for the parsing of the `gap` shorthand."""

    @staticmethod
    def resolve(data):
        gap = LengthParser.parse_gap(data)
        return [length(None, None) for length in gap]

    def test_a_single_length_applies_to_both_directions(self):
        assert self.resolve("8px") == [8, 8]

    def test_two_lengths_are_row_then_column(self):
        # The sizer expects them the other way around: (column, row)
        assert self.resolve("4px 8px") == [8, 4]

    def test_parse_none(self):
        """Test parsing None returns None."""
        assert LengthParser.parse_gap(None) is None

    def test_too_many_lengths_are_reported(self, caplog):
        assert LengthParser.parse_gap("1px 2px 3px") is None
        assert "expected 1 to 2 lengths" in caplog.text


class TestAlignmentParser:
    """Tests for AlignmentParser."""

    def test_parse_css_keywords(self):
        """The CSS `align-self` keywords map to the alignment values of the sizer."""
        assert AlignmentParser.parse('start') == 'min'
        assert AlignmentParser.parse('end') == 'max'
        assert AlignmentParser.parse('center') == 'center'
        assert AlignmentParser.parse('stretch') == 'expand'

    def test_parse_directional_aliases(self):
        """The directional aliases are just more readable spellings of start and end."""
        assert AlignmentParser.parse('left') == 'min'
        assert AlignmentParser.parse('top') == 'min'
        assert AlignmentParser.parse('right') == 'max'
        assert AlignmentParser.parse('bottom') == 'max'

    def test_parse_none_uses_default(self):
        """An unset alignment is left to the caller, which falls back on the skin and on the layout."""
        assert AlignmentParser.parse(None) is None
        assert AlignmentParser.parse(None, default='center') == 'center'

    def test_parse_invalid(self, caplog):
        """Test parsing invalid value."""
        assert AlignmentParser.parse("invalid") is None
        assert "Invalid alignment invalid" in caplog.text


class TestTextAlignmentParser:
    """Tests for TextAlignmentParser."""

    def test_parse_alignments(self):
        assert TextAlignmentParser.parse("left") == TextNode.A_boxed_left
        assert TextAlignmentParser.parse("center") == TextNode.A_boxed_center
        assert TextAlignmentParser.parse("right") == TextNode.A_boxed_right

    def test_parse_none_uses_default(self):
        """An unset text alignment is left to the caller, which falls back on the skin."""
        assert TextAlignmentParser.parse(None) is None
        assert TextAlignmentParser.parse(None, default=TextNode.A_boxed_center) == TextNode.A_boxed_center

    def test_parse_invalid(self, caplog):
        """Test parsing invalid value."""
        assert TextAlignmentParser.parse("invalid") is None
        assert "Invalid text align invalid" in caplog.text


class TestParsersCollection:
    """Tests for ParsersCollection."""

    def test_collection_has_all_parsers(self):
        """Test that collection provides access to all parsers."""
        parsers = ParsersCollection()

        assert isinstance(parsers.color, ColorParser)
        assert isinstance(parsers.length, LengthParser)
        assert isinstance(parsers.alignment, AlignmentParser)
        assert isinstance(parsers.text_alignment, TextAlignmentParser)
