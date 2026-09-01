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


"""Unit tests for the dock layouts, their sizing and their CSS-like box model."""

from cosmonium.ui.dock.layouts import LayoutDockWidget, SpaceDockWidget
from cosmonium.ui.loaders.parsers import AlignmentParser, LengthParser
from cosmonium.ui.skin import Selector, UIElement, UISkin, UISkinEntry

# For each tested property, the parsers used to convert the raw configuration values
# into the internal representation of the skin.
_PARSERS = {
    'align': AlignmentParser.parse,
    'justify': AlignmentParser.parse,
    'margin': LengthParser.parse_edge_lengths,
    'padding': LengthParser.parse_edge_lengths,
    'gap': LengthParser.parse_gap,
}


def make_skin(selector=None, **properties):
    """Build a skin with a single entry, whose properties are given as raw configuration values."""
    skin = UISkin()
    config = {name: _PARSERS.get(name, LengthParser.parse)(value) for name, value in properties.items()}
    skin.add_entry(UISkinEntry(selector or Selector(None, None, None, None), config))
    return skin


class FakeParent:
    """Mock layout parent."""

    def __init__(self, direction='horizontal', element=None):
        self.direction = direction
        self.element = element if element is not None else UIElement(type_='frame', class_='dock')

    def default_alignments(self):
        if self.direction == 'horizontal':
            return ('min', 'center')
        return ('center', 'min')


def make_layout(skin, direction='horizontal', **kwargs):
    """Build a layout and lay out its box, without creating the DirectGui frame drawing it."""
    layout = LayoutDockWidget(direction, [], **kwargs)
    layout.create_element(FakeParent(direction))
    layout.sizer.setup_content(skin)
    return layout


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
        skin = make_skin(font_size='12px')
        layout = make_layout(skin)
        spacer = SpaceDockWidget()

        spacer.add_to(None, layout, skin)

        assert layout.content_sizer.cells[0].alignments == ('min', 'center')

    def test_child_alignment_is_kept_when_requested(self):
        skin = make_skin(font_size='12px')
        layout = make_layout(skin)
        spacer = SpaceDockWidget(justify='max', align='max')

        spacer.add_to(None, layout, skin)

        assert layout.content_sizer.cells[0].alignments == ('max', 'max')

    def test_the_skin_alignment_is_used_when_the_configuration_sets_none(self):
        skin = make_skin(Selector('spacer', None, None, None), align='end')
        layout = make_layout(skin)
        spacer = SpaceDockWidget()

        spacer.add_to(None, layout, skin)

        # The horizontal alignment is still the default of the layout
        assert layout.content_sizer.cells[0].alignments == ('min', 'max')


class TestCellParameters:
    """A widget takes the parameters of its cell from the skin, unless its configuration overrides them."""

    def test_a_widget_with_nothing_set_has_no_margin_and_does_not_grow(self):
        skin = make_skin()
        layout = make_layout(skin)
        widget = SpaceDockWidget()
        widget.create_element(layout)

        parameters = widget.get_cell_parameters(layout, skin)

        assert parameters['borders'] == (0, 0, 0, 0)
        assert parameters['proportions'] == (0.0, 0.0)

    def test_the_margin_of_a_widget_comes_from_the_skin(self):
        skin = make_skin(Selector('spacer', None, None, None), margin='2px 4px')
        layout = make_layout(skin)
        widget = SpaceDockWidget()
        widget.create_element(layout)

        # DirectGUI order: left, right, bottom, top
        assert widget.get_cell_parameters(layout, skin)['borders'] == (4, 4, 2, 2)

    def test_the_configuration_of_a_widget_overrides_the_skin(self):
        skin = make_skin(Selector('spacer', None, None, None), margin='2px')
        layout = make_layout(skin)
        widget = SpaceDockWidget(margin=LengthParser.parse_edge_lengths('5px'))
        widget.create_element(layout)

        assert widget.get_cell_parameters(layout, skin)['borders'] == (5, 5, 5, 5)

    def test_a_margin_in_em_is_relative_to_the_font_size_of_the_widget(self):
        skin = make_skin(Selector('spacer', None, None, None), margin='0.5em', font_size='12px')
        layout = make_layout(skin)
        widget = SpaceDockWidget()
        widget.create_element(layout)

        assert widget.get_cell_parameters(layout, skin)['borders'] == (6, 6, 6, 6)

    def test_grow_claims_the_leftover_space_along_the_direction_of_the_parent(self):
        skin = make_skin()
        widget = SpaceDockWidget(grow=1.0)
        widget.create_element(FakeParent())

        horizontal = widget.get_cell_parameters(FakeParent('horizontal'), skin)
        vertical = widget.get_cell_parameters(FakeParent('vertical'), skin)

        assert horizontal['proportions'] == (1.0, 0.0)
        assert vertical['proportions'] == (0.0, 1.0)

    def test_a_widget_carries_its_structural_class_and_the_user_classes(self):
        widget = LayoutDockWidget('horizontal', [], class_='transparent', id_='main')

        assert widget.element.class_ == frozenset(('layout', 'transparent'))
        assert widget.element.id_ == 'main'


class TestContentInset:
    """A container insets its own content, the children never carry the padding of their parent."""

    def test_the_content_is_inset_by_the_border_and_the_padding(self):
        skin = make_skin(Selector('frame', None, 'layout', None), border_width='2px', padding='3px 6px')
        layout = make_layout(skin)

        assert layout.sizer.get_content_inset(skin) == (8, 8, 5, 5)

    def test_the_content_of_a_bare_container_is_not_inset(self):
        skin = make_skin(Selector('frame', None, 'layout', None))
        layout = make_layout(skin)

        assert layout.sizer.get_content_inset(skin) == (0, 0, 0, 0)

    def test_rounded_corners_widen_the_inset_so_the_content_avoids_them(self):
        skin = make_skin(Selector('frame', None, 'layout', None), border_width='10px', border_radius='50px')
        layout = make_layout(skin)

        # 50 - (50 - 10) * cos(45), the thickness of the border in the diagonal direction
        assert layout.sizer.get_content_inset(skin)[0] == 50 - 40 * 0.5**0.5

    def test_the_padding_of_the_configuration_overrides_the_skin(self):
        skin = make_skin(Selector('frame', None, 'layout', None), padding='3px')
        layout = make_layout(skin, padding=LengthParser.parse_edge_lengths('7px'))

        assert layout.sizer.get_content_inset(skin) == (7, 7, 7, 7)

    def test_the_padding_grows_the_layout_around_its_content(self):
        skin = make_skin(Selector('frame', None, 'layout', None), padding='4px')
        layout = make_layout(skin)
        layout.content_sizer.add((16, 16))
        layout.update_layout()

        assert layout.sizer.get_size() == (24, 24)
        assert layout.content_sizer.get_size() == (16, 16)


class TestGap:
    """The space between the children of a layout."""

    def test_the_gap_between_the_children_comes_from_the_skin(self):
        skin = make_skin(Selector('frame', None, 'layout', None), gap='4px 8px')
        layout = make_layout(skin)

        assert layout.content_sizer.gaps == (8, 4)

    def test_the_gap_of_the_configuration_overrides_the_skin(self):
        skin = make_skin(Selector('frame', None, 'layout', None), gap='4px')
        layout = make_layout(skin, gap=LengthParser.parse_gap('9px'))

        assert layout.content_sizer.gaps == (9, 9)

    def test_the_gap_separates_the_children(self):
        skin = make_skin(Selector('frame', None, 'layout', None), gap='4px')
        layout = make_layout(skin)
        layout.content_sizer.add((16, 16))
        layout.content_sizer.add((16, 16))
        layout.update_layout()

        assert layout.sizer.get_size() == (36, 16)


class TestDeclaredSize:
    """The size declared by the skin is the minimum size of the border box of the layout."""

    def test_layout_is_sized_by_its_content_by_default(self):
        layout = make_layout(make_skin())
        layout.content_sizer.add((16, 16))
        layout.update_layout()

        assert layout.sizer.get_size() == (16, 16)

    def test_declared_size_is_a_minimum(self):
        layout = make_layout(make_skin(Selector('frame', None, 'layout', None), height='48px'))
        layout.content_sizer.add((16, 16))
        layout.update_layout()

        assert layout.sizer.get_size() == (16, 48)

    def test_content_larger_than_the_declared_size_grows_the_layout(self):
        layout = make_layout(make_skin(Selector('frame', None, 'layout', None), height='16px'))
        layout.content_sizer.add((16, 64))
        layout.update_layout()

        assert layout.sizer.get_size() == (16, 64)

    def test_widgets_are_centered_across_the_declared_size(self):
        """The row of widgets fills the layout, each widget is then placed by its own alignment."""
        layout = make_layout(make_skin(Selector('frame', None, 'layout', None), height='48px'))
        layout.content_sizer.add((16, 16), alignments=layout.default_alignments())
        layout.update_layout()

        cell = layout.content_sizer.cells[0]
        assert cell.get_size() == (16, 48)

    def test_the_declared_size_includes_the_padding(self):
        """As with a CSS `border-box` sizing, the declared size is that of the whole box."""
        layout = make_layout(make_skin(Selector('frame', None, 'layout', None), height='48px', padding='4px'))
        layout.content_sizer.add((16, 16))
        layout.update_layout()

        assert layout.sizer.get_size() == (24, 48)
        assert layout.content_sizer.get_size() == (16, 40)


class TestSpacer:
    """A spacer reserves empty space, sized by the skin or by its own configuration."""

    def test_spacer_resolves_pixel_lengths(self):
        skin = make_skin(font_size='12px')
        layout = make_layout(skin)
        spacer = SpaceDockWidget(width=LengthParser.parse('10px'), height=LengthParser.parse('4px'))

        spacer.add_to(None, layout, skin)

        assert spacer.widget == (10, 4)

    def test_spacer_resolves_em_against_its_font_size(self):
        skin = make_skin(font_size='12px')
        layout = make_layout(skin)
        spacer = SpaceDockWidget(width=LengthParser.parse('2em'))

        spacer.add_to(None, layout, skin)

        assert spacer.widget == (24, 0)

    def test_spacer_size_comes_from_the_skin_when_unset(self):
        skin = make_skin(Selector('spacer', None, None, None), width='8px', height='2px')
        layout = make_layout(skin)
        spacer = SpaceDockWidget()

        spacer.add_to(None, layout, skin)

        assert spacer.widget == (8, 2)

    def test_a_spacer_with_no_size_at_all_reserves_nothing(self):
        skin = make_skin(font_size='12px')
        layout = make_layout(skin)
        spacer = SpaceDockWidget()

        spacer.add_to(None, layout, skin)

        assert spacer.widget == (0, 0)
