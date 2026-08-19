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


"""Unit tests for the dock layouts."""

from directguilayout.gui import Sizer

from cosmonium.ui.dock.layouts import LayoutDockWidget, SpaceDockWidget
from cosmonium.ui.loaders.parsers import LengthParser
from cosmonium.ui.skin import Selector, UISkin, UISkinEntry


def update_layout(layout):
    """Update the internal size of the given layout, skipping the update of its DirectFrame."""
    Sizer.update(layout.sizer, layout.sizer.update_min_size())


def make_skin(**config):
    """Build a skin with a single entry with the given properties and with empty selector."""
    skin = UISkin()
    entry = UISkinEntry(Selector(None, None, None, None), {})
    for key, value in config.items():
        setattr(entry, key, value)
    skin.add_entry(entry)
    return skin


class TestDefaultAlignments:
    """The alignment given to the children that do not request one."""

    def test_horizontal_layout_centers_its_children_vertically(self):
        layout = LayoutDockWidget('horizontal', [])

        assert layout.default_alignments() == ('min', 'center')

    def test_vertical_layout_centers_its_children_horizontally(self):
        layout = LayoutDockWidget('vertical', [])

        assert layout.default_alignments() == ('center', 'min')


class TestChildAlignment:
    """A child that does not request an alignment gets the default one from the parent layout."""

    def test_child_without_alignment_uses_the_layout_default(self):
        skin = make_skin(font_size=LengthParser.parse('12px'))
        layout = LayoutDockWidget('horizontal', [])
        spacer = SpaceDockWidget(None, None)

        spacer.add_to(None, layout, None, skin)

        assert layout.sizer.cells[0].alignments == ('min', 'center')

    def test_child_alignment_is_kept_when_requested(self):
        skin = make_skin(font_size=LengthParser.parse('12px'))
        layout = LayoutDockWidget('horizontal', [])
        spacer = SpaceDockWidget(None, None, alignments=('max', 'max'))

        spacer.add_to(None, layout, None, skin)

        assert layout.sizer.cells[0].alignments == ('max', 'max')


class TestDeclaredSize:
    """The size declared by the skin is used as the minimum size for the internal sizer of the layout."""

    def test_layout_is_sized_by_its_content_by_default(self):
        layout = LayoutDockWidget('horizontal', [])
        layout.sizer.set_declared_size((0, 0))
        layout.sizer.add((16, 16))
        update_layout(layout)

        assert layout.sizer.get_size() == (16, 16)

    def test_declared_size_is_a_minimum(self):
        layout = LayoutDockWidget('horizontal', [])
        layout.sizer.set_declared_size((0, 48))
        layout.sizer.add((16, 16))
        update_layout(layout)

        assert layout.sizer.get_size() == (16, 48)

    def test_content_larger_than_the_declared_size_grows_the_layout(self):
        layout = LayoutDockWidget('horizontal', [])
        layout.sizer.set_declared_size((0, 16))
        layout.sizer.add((16, 64))
        update_layout(layout)

        assert layout.sizer.get_size() == (16, 64)

    def test_widgets_are_centered_across_the_declared_size(self):
        """The row of widgets fills the layout, each widget is then placed by its own alignment."""
        layout = LayoutDockWidget('horizontal', [])
        layout.sizer.set_declared_size((0, 48))
        inner = Sizer('horizontal')
        inner.default_size = (16, 16)
        layout.sizer.add(inner, alignments=layout.default_alignments())
        update_layout(layout)

        cell = layout.sizer.cells[0]
        assert cell.get_size() == (16, 48)
        # (48 - 16) / 2
        assert cell.object_offset == (0, 16)


class TestSpacer:
    """A spacer resolves its lengths using the parent layout."""

    def test_spacer_resolves_pixel_lengths(self):
        skin = make_skin(font_size=LengthParser.parse('12px'))
        layout = LayoutDockWidget('horizontal', [])
        spacer = SpaceDockWidget(LengthParser.parse('10px'), LengthParser.parse('4px'))

        spacer.add_to(None, layout, None, skin)

        assert spacer.widget == (10, 4)

    def test_spacer_resolves_em_against_the_layout_font_size(self):
        skin = make_skin(font_size=LengthParser.parse('12px'))
        layout = LayoutDockWidget('horizontal', [])
        spacer = SpaceDockWidget(LengthParser.parse('2em'), None)

        spacer.add_to(None, layout, None, skin)

        assert spacer.widget == (24, 0)
