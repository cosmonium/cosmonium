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


"""Unit tests for the CSS-like skin/selector."""

from cosmonium.ui.skin import ParentSelector, Selector, UIElement, UISkin, UISkinEntry


def make_entry(selector, **config):
    entry = UISkinEntry(selector, {})
    for key, value in config.items():
        setattr(entry, key, value)
    return entry


class TestSelector:
    def test_selector_with_all_none_matches_any_element(self):
        selector = Selector(type_=None, state=None, class_=None, id_=None)
        element = UIElement(type_='button', class_='primary', id_='ok')

        assert selector.applicable(element, state=None) is True

    def test_selector_matches_on_type(self):
        selector = Selector(type_='button', state=None, class_=None, id_=None)

        assert selector.applicable(UIElement(type_='button'), state=None) is True
        assert selector.applicable(UIElement(type_='label'), state=None) is False

    def test_selector_matches_on_class_and_id_together(self):
        selector = Selector(type_=None, state=None, class_='primary', id_='ok')

        assert selector.applicable(UIElement(type_='button', class_='primary', id_='ok'), state=None) is True
        assert selector.applicable(UIElement(type_='button', class_='primary', id_='cancel'), state=None) is False
        assert selector.applicable(UIElement(type_='button', class_='secondary', id_='ok'), state=None) is False

    def test_selector_matches_on_state(self):
        selector = Selector(type_='button', state='hover', class_=None, id_=None)
        element = UIElement(type_='button')

        assert selector.applicable(element, state='hover') is True
        assert selector.applicable(element, state=None) is False
        assert selector.applicable(element, state='clicked') is False


class TestParentSelector:
    def test_parent_selector_matches_when_an_ancestor_satisfies_the_parent_selector(self):
        parent_selector = Selector(type_='frame', state=None, class_=None, id_=None)
        own_selector = Selector(type_='button', state=None, class_=None, id_=None)
        selector = ParentSelector(parent_selector, own_selector)

        grandparent = UIElement(type_='frame')
        parent = UIElement(type_='sizer', parent=grandparent)
        element = UIElement(type_='button', parent=parent)

        assert selector.applicable(element, state=None) is True

    def test_parent_selector_does_not_match_when_own_selector_fails(self):
        parent_selector = Selector(type_='frame', state=None, class_=None, id_=None)
        own_selector = Selector(type_='label', state=None, class_=None, id_=None)
        selector = ParentSelector(parent_selector, own_selector)

        parent = UIElement(type_='frame')
        element = UIElement(type_='button', parent=parent)

        assert selector.applicable(element, state=None) is False

    def test_parent_selector_does_not_match_when_no_ancestor_satisfies_it(self):
        parent_selector = Selector(type_='frame', state=None, class_=None, id_=None)
        own_selector = Selector(type_='button', state=None, class_=None, id_=None)
        selector = ParentSelector(parent_selector, own_selector)

        root = UIElement(type_='window')
        element = UIElement(type_='button', parent=root)

        assert selector.applicable(element, state=None) is False

    def test_parent_selector_with_no_parent_at_all_does_not_match(self):
        parent_selector = Selector(type_='frame', state=None, class_=None, id_=None)
        own_selector = Selector(type_='button', state=None, class_=None, id_=None)
        selector = ParentSelector(parent_selector, own_selector)

        element = UIElement(type_='button', parent=None)

        assert selector.applicable(element, state=None) is False


class TestSelectorSpecificity:
    """Tests for Selector.specificity()."""

    def test_empty_selector_has_zero_specificity(self):
        selector = Selector(None, None, None, None)
        assert selector.specificity() == (0, 0, 0)

    def test_type_only(self):
        selector = Selector('button', None, None, None)
        assert selector.specificity() == (0, 0, 1)

    def test_class_only(self):
        selector = Selector(None, None, 'primary', None)
        assert selector.specificity() == (0, 1, 0)

    def test_state_only(self):
        selector = Selector(None, 'hover', None, None)
        assert selector.specificity() == (0, 1, 0)

    def test_id_only(self):
        selector = Selector(None, None, None, 'ok')
        assert selector.specificity() == (1, 0, 0)

    def test_id_outweighs_class_and_type(self):
        id_selector = Selector(None, None, None, 'ok')
        class_and_type_selector = Selector('button', 'hover', 'primary', None)
        assert id_selector.specificity() > class_and_type_selector.specificity()

    def test_class_outweighs_type(self):
        class_selector = Selector(None, None, 'primary', None)
        type_selector = Selector('button', None, None, None)
        assert class_selector.specificity() > type_selector.specificity()

    def test_parent_selector_accumulates_specificity(self):
        selector = ParentSelector(Selector(None, None, None, 'hud'), Selector('button', None, None, None))
        # id (from parent) + type (from own selector)
        assert selector.specificity() == (1, 0, 1)


class TestCascade:
    """Tests for UISkin.collect_entries_for's specificity-based cascade."""

    def test_id_selector_wins_over_later_type_selector(self):
        skin = UISkin()
        skin.add_entry(UISkinEntry(Selector('button', None, None, 'ok'), {'text_color': 'from-id'}))
        skin.add_entry(UISkinEntry(Selector('button', None, None, None), {'text_color': 'from-type'}))

        result = skin.get(UIElement(type_='button', id_='ok'))

        assert result.text_color == 'from-id'

    def test_class_selector_wins_over_type_selector_regardless_of_order(self):
        skin = UISkin()
        # Declared after the class rule, but less specific: must not win.
        skin.add_entry(UISkinEntry(Selector('button', None, 'primary', None), {'text_color': 'from-class'}))
        skin.add_entry(UISkinEntry(Selector('button', None, None, None), {'text_color': 'from-type'}))

        result = skin.get(UIElement(type_='button', class_='primary'))

        assert result.text_color == 'from-class'

    def test_equal_specificity_later_declaration_wins(self):
        skin = UISkin()
        skin.add_entry(UISkinEntry(Selector('button', None, None, None), {'text_color': 'first'}))
        skin.add_entry(UISkinEntry(Selector('button', None, None, None), {'text_color': 'second'}))

        result = skin.get(UIElement(type_='button'))

        assert result.text_color == 'second'

    def test_non_matching_entries_are_ignored(self):
        skin = UISkin()
        skin.add_entry(UISkinEntry(Selector('label', None, None, None), {'text_color': 'from-label'}))

        result = skin.get(UIElement(type_='button'))

        assert result.text_color is None

    def test_only_property_set_by_higher_specificity_entry_is_overridden(self):
        skin = UISkin()
        skin.add_entry(UISkinEntry(Selector(None, None, None, None), {'text_color': 'base', 'font_family': 'Sans'}))
        skin.add_entry(UISkinEntry(Selector('button', None, None, 'ok'), {'text_color': 'from-id'}))

        result = skin.get(UIElement(type_='button', id_='ok'))

        # Higher-specificity rule overrides text_color, but doesn't touch font_family.
        assert result.text_color == 'from-id'
        assert result.font_family == 'Sans'


class TestSkinEntry:
    def test_skin_entry_getattr_returns_none_for_unset_property(self):
        entry = UISkinEntry(Selector(None, None, None, None), {})

        assert entry.background_color is None

    def test_skin_entry_setattr_ignores_none_values(self):
        entry = UISkinEntry(Selector(None, None, None, None), {'text_color': 'red'})

        entry.text_color = None

        assert entry.text_color == 'red'

    def test_skin_entry_setattr_stores_non_none_values(self):
        entry = UISkinEntry(Selector(None, None, None, None), {})

        entry.text_color = 'blue'

        assert entry.text_color == 'blue'

    def test_skin_entry_update_merges_and_overrides_config_from_another_entry(self):
        base = UISkinEntry(Selector(None, None, None, None), {'text_color': 'red', 'font_family': 'sans'})
        override = UISkinEntry(Selector(None, None, None, None), {'text_color': 'blue'})

        base.update(override)

        assert base.text_color == 'blue'
        assert base.font_family == 'sans'


class TestSkinCascade:
    def test_collect_entries_for_merges_in_declaration_order_last_match_wins(self):
        skin = UISkin()
        skin.add_entry(make_entry(Selector('button', None, None, None), text_color='red', font_family='sans'))
        skin.add_entry(make_entry(Selector('button', None, 'primary', None), text_color='blue'))

        element = UIElement(type_='button', class_='primary')
        style = skin.collect_entries_for(element, state=None)

        assert style.text_color == 'blue'
        assert style.font_family == 'sans'

    def test_collect_entries_for_ignores_non_matching_entries(self):
        skin = UISkin()
        skin.add_entry(make_entry(Selector('label', None, None, None), text_color='green'))

        element = UIElement(type_='button')
        style = skin.collect_entries_for(element, state=None)

        assert style.text_color is None

    def test_get_returns_same_result_as_collect_entries_for(self):
        skin = UISkin()
        skin.add_entry(make_entry(Selector('button', None, None, None), text_color='red'))
        element = UIElement(type_='button')

        assert skin.get(element).text_color == skin.collect_entries_for(element, None).text_color


class TestInheritance:
    """Tests for the inheritance of text-related properties from ancestor elements."""

    def test_text_color_inherits_from_parent(self):
        skin = UISkin()
        skin.add_entry(UISkinEntry(Selector(None, None, 'hud', None), {'text_color': 'hud-color'}))
        parent = UIElement(type_='frame', class_='hud')
        child = UIElement(type_='button', parent=parent)

        result = skin.get(child)

        assert result.text_color == 'hud-color'

    def test_inheritance_recurses_through_multiple_ancestors(self):
        skin = UISkin()
        skin.add_entry(UISkinEntry(Selector(None, None, 'hud', None), {'font_family': 'Sans'}))
        grandparent = UIElement(type_='frame', class_='hud')
        parent = UIElement(type_='frame', parent=grandparent)
        child = UIElement(type_='button', parent=parent)

        result = skin.get(child)

        assert result.font_family == 'Sans'

    def test_own_matching_entry_takes_precedence_over_inheritance(self):
        skin = UISkin()
        skin.add_entry(UISkinEntry(Selector(None, None, 'hud', None), {'text_color': 'hud-color'}))
        skin.add_entry(UISkinEntry(Selector('button', None, None, None), {'text_color': 'button-color'}))
        parent = UIElement(type_='frame', class_='hud')
        child = UIElement(type_='button', parent=parent)

        result = skin.get(child)

        assert result.text_color == 'button-color'

    def test_non_inheritable_properties_do_not_propagate(self):
        skin = UISkin()
        skin.add_entry(UISkinEntry(Selector(None, None, 'hud', None), {'background_color': 'hud-bg'}))
        parent = UIElement(type_='frame', class_='hud')
        child = UIElement(type_='button', parent=parent)

        result = skin.get(child)

        assert result.background_color is None

    def test_root_element_without_parent_has_no_inherited_value(self):
        skin = UISkin()
        result = skin.get(UIElement(type_='frame'))

        assert result.text_color is None

    def test_inheritance_ignores_the_child_state(self):
        skin = UISkin()
        skin.add_entry(UISkinEntry(Selector(None, None, 'hud', None), {'text_color': 'default'}))
        skin.add_entry(UISkinEntry(Selector(None, 'hover', 'hud', None), {'text_color': 'parent-hover'}))
        parent = UIElement(type_='frame', class_='hud')
        child = UIElement(type_='button', parent=parent)

        # The child is hovered, but that doesn't make the parent "hovered" too.
        result = skin.get(child, state='hover')

        assert result.text_color == 'default'


class TestMultiClassSelectors:
    """Tests for compound class selectors."""

    def test_element_with_single_class_string_still_matches(self):
        selector = Selector('button', None, 'primary', None)
        element = UIElement(type_='button', class_='primary')

        assert selector.applicable(element, None)

    def test_selector_requires_all_listed_classes(self):
        selector = Selector('button', None, ['primary', 'large'], None)

        assert selector.applicable(UIElement(type_='button', class_=['primary', 'large']), None)
        assert not selector.applicable(UIElement(type_='button', class_='primary'), None)
        assert not selector.applicable(UIElement(type_='button', class_=None), None)

    def test_element_may_have_extra_classes_not_required_by_selector(self):
        selector = Selector('button', None, 'primary', None)
        element = UIElement(type_='button', class_=['primary', 'large'])

        assert selector.applicable(element, None)

    def test_compound_class_specificity_counts_each_class(self):
        single = Selector('button', None, 'primary', None)
        compound = Selector('button', None, ['primary', 'large'], None)

        assert compound.specificity() > single.specificity()
        assert compound.specificity() == (0, 2, 1)

    def test_compound_selector_wins_cascade_over_single_class_selector(self):
        skin = UISkin()
        skin.add_entry(UISkinEntry(Selector('button', None, 'primary', None), {'text_color': 'single'}))
        skin.add_entry(UISkinEntry(Selector('button', None, ['primary', 'large'], None), {'text_color': 'compound'}))

        result = skin.get(UIElement(type_='button', class_=['primary', 'large']))

        assert result.text_color == 'compound'


def _fixed(value):
    return lambda element, font_size, skin: value


class TestSkinGetStyle:
    def test_get_style_for_button_maps_colors_and_font(self):
        skin = UISkin()
        skin.add_entry(
            make_entry(
                Selector('button', None, None, None),
                background_color='bg',
                text_color='fg',
                font_family='sans',
                font_style='normal',
                font_weight='normal',
                font_size=_fixed(12),
            )
        )
        element = UIElement(type_='button')

        params = skin.get_style(element)

        assert params['frameColor'] == 'bg'
        assert params['text_fg'] == 'fg'

    def test_get_style_for_frame_only_maps_background_color(self):
        skin = UISkin()
        skin.add_entry(make_entry(Selector('frame', None, None, None), background_color='bg', font_size=_fixed(12)))
        element = UIElement(type_='frame')

        params = skin.get_style(element)

        assert params == {'frameColor': 'bg'}

    def test_get_style_applies_prefix_to_every_parameter_key(self):
        skin = UISkin()
        skin.add_entry(make_entry(Selector('frame', None, None, None), background_color='bg', font_size=_fixed(12)))
        element = UIElement(type_='frame')

        params = skin.get_style(element, prefix='inner_')

        assert params == {'inner_frameColor': 'bg'}
