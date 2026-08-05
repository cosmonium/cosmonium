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
