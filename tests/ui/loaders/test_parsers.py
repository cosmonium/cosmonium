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
from panda3d.core import LVector4, TextNode

from cosmonium.ui.loaders.parsers import (
    AlignmentParser,
    BorderParser,
    ColorParser,
    GapParser,
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


class TestLengthParser:
    """Tests for LengthParser."""

    @staticmethod
    def make_skin(root_font_size=16, **entry_config):
        """Build a skin whose single entry, matching any element, holds the given properties."""
        skin = UISkin()
        skin.root_font_size = root_font_size
        entry = UISkinEntry(Selector(None, None, None, None), {})
        for key, value in entry_config.items():
            setattr(entry, key, value)
        skin.add_entry(entry)
        return skin

    def test_parse_pixels(self):
        """Test parsing pixel values."""
        parser = LengthParser()

        size_fn = parser.parse("16px")
        assert size_fn(None, None) == 16

    def test_parse_em(self):
        """Test parsing em values, relative to the font size of the element."""
        parser = LengthParser()
        skin = self.make_skin(font_size=parser.parse("12px"))
        element = UIElement('button')

        size_fn = parser.parse("1.5em")
        assert size_fn(element, skin) == 18

    def test_parse_em_of_font_size_is_relative_to_the_parent(self):
        """For font-size property, em is relative to the parent's font size."""
        parser = LengthParser()
        skin = self.make_skin(font_size=parser.parse("12px"))
        element = UIElement('button', parent=UIElement('frame'))

        size_fn = parser.parse("1.5em", relative_to_parent=True)
        assert size_fn(element, skin) == 18

    def test_parse_em_falls_back_to_the_root_font_size(self):
        """An em length applied to an element who has no defined font size, uses the root font size."""
        parser = LengthParser()
        skin = self.make_skin(root_font_size=20)

        size_fn = parser.parse("1.5em")
        assert size_fn(UIElement('button'), skin) == 30

    def test_parse_rem(self):
        """Test parsing rem values, relative to the skin's root font size."""
        parser = LengthParser()
        skin = self.make_skin(root_font_size=20)

        size_fn = parser.parse("1.5rem")
        assert size_fn(None, skin) == 30

    def test_parse_invalid_string_does_not_crash(self, caplog):
        """A string containing an invalid unit should be reported."""
        parser = LengthParser()

        size_fn = parser.parse("1x")
        assert size_fn is None
        assert "Invalid size 1x" in caplog.text

    def test_parse_numeric(self):
        """Test parsing numeric values."""
        parser = LengthParser()

        size_fn = parser.parse(20)
        assert size_fn(None, None) == 20

        size_fn = parser.parse(15.5)
        assert size_fn(None, None) == 15.5

    def test_parse_none(self):
        """Test parsing None returns None."""
        parser = LengthParser()
        assert parser.parse(None) is None

    def test_parse_edge_lengths_single(self):
        """Test parsing single edge length (all edges same)."""
        parser = LengthParser()

        lengths = parser.parse_edge_lengths("10px")
        assert len(lengths) == 4
        for length in lengths:
            assert length(None, None) == 10

    def test_parse_edge_lengths_two(self):
        """Test parsing two edge lengths (vertical horizontal)."""
        parser = LengthParser()

        lengths = parser.parse_edge_lengths("10px 20px")
        assert len(lengths) == 4
        # DirectGUI order: left, right, bottom, top
        assert lengths[0](None, None) == 20  # left
        assert lengths[1](None, None) == 20  # right
        assert lengths[2](None, None) == 10  # bottom
        assert lengths[3](None, None) == 10  # top

    def test_parse_edge_lengths_none(self):
        """Test parsing None returns None."""
        parser = LengthParser()
        assert parser.parse_edge_lengths(None) is None


class TestAlignmentParser:
    """Tests for AlignmentParser."""

    def test_parse_left_top(self):
        """Test parsing left/top alignments."""
        parser = AlignmentParser()
        result = parser.parse(['left', 'top'])
        assert result == ['min', 'min']

    def test_parse_right_bottom(self):
        """Test parsing right/bottom alignments."""
        parser = AlignmentParser()
        result = parser.parse(['right', 'bottom'])
        assert result == ['max', 'max']

    def test_parse_center(self):
        """Test parsing center alignments."""
        parser = AlignmentParser()
        result = parser.parse(['center', 'center'])
        assert result == ['center', 'center']

    def test_parse_none_uses_default(self):
        """Test parsing None returns default."""
        parser = AlignmentParser()
        result = parser.parse(None, default=('max', 'min'))
        assert result == ('max', 'min')

    def test_parse_none_without_default_is_unspecified(self):
        """With no default, an unspecified alignment stays unspecified."""
        parser = AlignmentParser()
        assert parser.parse(None) is None

    def test_parse_invalid(self, caplog):
        """Test parsing invalid value."""
        parser = AlignmentParser()
        result = parser.parse("invalid", default=('min', 'min'))
        assert result == ('min', 'min')  # Should return default
        assert "Invalid alignments" in caplog.text


class TestBorderParser:
    """Tests for BorderParser."""

    def test_parse_list(self):
        """Test parsing border list."""
        parser = BorderParser()
        border = parser.parse([1, 2, 3, 4])
        assert isinstance(border, LVector4)
        assert border.x == 1
        assert border.y == 2
        assert border.z == 3
        assert border.w == 4

    def test_parse_single_value(self):
        """Test parsing single border value (all sides same)."""
        parser = BorderParser()
        border = parser.parse(5)
        assert isinstance(border, LVector4)
        assert border.x == 5
        assert border.y == 5
        assert border.z == 5
        assert border.w == 5

    def test_parse_none(self):
        """Test parsing None returns None."""
        parser = BorderParser()
        assert parser.parse(None) is None

    def test_parse_invalid(self, caplog):
        """Test parsing invalid value."""
        parser = BorderParser()
        border = parser.parse([1, 2])  # Too few values
        assert border is None
        assert "Invalid borders" in caplog.text


class TestGapParser:
    """Tests for GapParser."""

    def test_parse_list(self):
        """Test parsing gap list."""
        parser = GapParser()
        gap = parser.parse([5, 10])
        assert gap == (5, 10)

    def test_parse_single_value(self):
        """Test parsing single gap value (both directions same)."""
        parser = GapParser()
        gap = parser.parse(8)
        assert gap == (8, 8)

    def test_parse_none_uses_default(self):
        """Test parsing None returns default."""
        parser = GapParser()
        gap = parser.parse(None, default=(3, 7))
        assert gap == (3, 7)

    def test_parse_invalid(self, caplog):
        """Test parsing invalid value."""
        parser = GapParser()
        gap = parser.parse("invalid")
        assert gap == (0, 0)  # Should return default
        assert "Invalid gaps" in caplog.text


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
        assert isinstance(parsers.border, BorderParser)
        assert isinstance(parsers.gap, GapParser)
        assert isinstance(parsers.text_alignment, TextAlignmentParser)
