# -*- coding: utf-8 -*-
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


from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, FrozenSet, Iterable, Optional, Tuple, Union

from panda3d.core import LColor

from .. import settings
from ..fonts import Font, fontsManager

logger = logging.getLogger("ui")


def normalize_classes(value: Union[None, str, Iterable[str]]) -> Optional[FrozenSet[str]]:
    """
    Normalize a `class` value (single string, list of strings, or None) into a frozenset.

    Args:
        value: A class name, an iterable of class names (CSS-like compound class, all of
            which must be present for a selector to match), or None (no class constraint)

    Returns:
        A frozenset of class names, or None if no class was specified
    """
    if value is None:
        return None
    if isinstance(value, str):
        return frozenset((value,))
    return frozenset(value)


def combine_classes(*values: Union[None, str, Iterable[str]]) -> Optional[FrozenSet[str]]:
    """
    Merge several `class` values (each a class name, iterable of class names, or None) into one frozenset.

    Used to combine a widget's own structural class, to let skins target its internal parts,
    with extra classes a user attached to that widget in its configuration.

    Args:
        *values: Any number of class specs, as accepted by `normalize_classes`

    Returns:
        A frozenset of all class names found, or None if none were specified
    """
    classes = set()
    for value in values:
        normalized = normalize_classes(value)
        if normalized:
            classes.update(normalized)
    return frozenset(classes) if classes else None


def report_error(message: str, context: Optional[str] = None) -> None:
    """
    Report a skin-related parsing or resolution error.

    Args:
        message: Description of the error
        context: Optional extra context (e.g. file, entry index, selector) to help
            locate the offending skin data
    """
    if context:
        logger.warning(f"{message} ({context})")
    else:
        logger.warning(message)


# Properties that inherit from an ancestor element's resolved style when an element (and none of its matching entries)
# sets them
INHERITED_PROPERTIES = ('text_color', 'font_family', 'font_size', 'font_style', 'font_weight', 'text_align')

# CSS-like alignment keywords, mapped to the alignment values understood by the DirectGuiLayout sizer.
#
# `stretch` resizes the element to fill its cell, the three other values keep the element at its
# natural size and place it at the start, the end or the center of the cell.
ALIGNMENT_VALUES = {
    'start': 'min',
    'end': 'max',
    'center': 'center',
    'stretch': 'expand',
    # Directional aliases, more readable than start/end: `left` and `right` for the horizontal
    # alignment (`justify`), `top` and `bottom` for the vertical one (`align`).
    # They are scoped by the loader
    'left': 'min',
    'right': 'max',
    'top': 'min',
    'bottom': 'max',
}


def calc_size_px(size, element, skin):
    """Resolve a length given in "px", scaled by the global UI scale factor."""
    return size * settings.ui_scale


def calc_size_rem(size, element, skin):
    """Resolve a length given in "rem", relative to the skin's root font size."""
    return skin.root_font_size * settings.ui_scale * size


def calc_size_em(size, element, skin):
    """Resolve a length given in "em", relative to the font size of the element it applies to."""
    return skin.get(element).resolved_font_size(element, skin) * size


def calc_font_size_em(size, element, skin):
    """
    Resolve a `font-size` property given in "em".

    When specified in "em", the font size is relative to the parent element's font size, falling
    back to the root font size for an element without a parent.
    """
    if element is None or element.parent is None:
        return skin.root_font_size * settings.ui_scale * size
    return skin.get(element.parent).resolved_font_size(element.parent, skin) * size


def resolve_length(length: Optional[Callable], element: UIElement, skin: UISkin, default: float = 0.0) -> float:
    """
    Trivial method to resolve a single length property into pixels.

    Args:
        length: A length callable, as returned by the length parser, or None when unset
        element: The element the length belongs to
        skin: The skin resolving the element's style
        default: Value to return when the length is unset

    Returns:
        The length in pixels
    """
    if length is None:
        return default
    return length(element, skin)


def resolve_gap(
    gap: Optional[Tuple[Optional[Callable], Optional[Callable]]], element: UIElement, skin: UISkin
) -> Tuple[float, float]:
    """
    Resolve a `gap`, the spacing between the children of a container, into pixels.

    Args:
        gap: The (column, row) gaps, in the order expected by the sizer, or None
        element: The element the gap belongs to
        skin: The skin resolving the element's style

    Returns:
        The (column, row) gaps in pixels
    """
    if gap is None:
        return (0.0, 0.0)
    column, row = gap
    return (resolve_length(column, element, skin), resolve_length(row, element, skin))


def resolve_edge_lengths(
    lengths: Optional[Iterable[Optional[Callable]]], element: UIElement, skin: UISkin, default: float = 0.0
) -> Tuple[float, float, float, float]:
    """
    Resolve the four edge lengths of a box into pixels.

    Args:
        lengths: The four edge lengths, in DirectGUI order (left, right, bottom, top), or None
        element: The element the lengths belong to
        skin: The skin resolving the element's style
        default: Value to use for the edges that are unset

    Returns:
        The four edge lengths in pixels, in DirectGUI order (left, right, bottom, top)
    """
    if lengths is None:
        return (default,) * 4
    return tuple(resolve_length(length, element, skin, default) for length in lengths)


@dataclass
class UIElement:
    type_: str
    parent: Optional[UIElement] = None
    class_: Union[None, str, Iterable[str]] = None
    id_: Optional[str] = None

    def __post_init__(self):
        self.class_ = normalize_classes(self.class_)


class Selector:
    def __init__(self, type_, state, class_, id_):
        self.type_ = type_
        # Internally, states are managed as classes
        self.state = normalize_classes(state)
        self.class_ = normalize_classes(class_)
        self.id_ = id_

    def applicable(self, element, state):
        active_states = normalize_classes(state) or frozenset()
        return (
            (self.type_ is None or self.type_ == element.type_)
            and (self.state is None or self.state.issubset(active_states))
            and (self.class_ is None or self.class_.issubset(element.class_ or frozenset()))
            and (self.id_ is None or self.id_ == element.id_)
        )

    def specificity(self) -> tuple[int, int, int]:
        """
        CSS-like specificity as an (id, class-or-state, type) tuple, higher wins.

        Mirrors CSS (id, class/attribute/pseudo-class, type) ordering: an id
        match outweighs any number of class/state matches, which in turn
        outweigh a type match. A compound class or pseudo-class selector (multiple
        required classes or states) contributes one point per class or state.
        """
        class_count = len(self.class_) if self.class_ else 0
        state_count = len(self.state) if self.state else 0
        return (
            1 if self.id_ is not None else 0,
            class_count + state_count,
            1 if self.type_ is not None else 0,
        )


class ParentSelector:
    def __init__(self, parent, selector):
        self.parent = parent
        self.selector = selector

    def applicable(self, element, state):
        if self.selector.applicable(element, state):
            element = element.parent
            while element is not None:
                if self.parent.applicable(element, None):
                    return True
                element = element.parent
        return False

    def specificity(self) -> tuple[int, int, int]:
        """Specificity accumulates across the whole selector chain, like a CSS compound selector."""
        own = self.selector.specificity()
        parent = self.parent.specificity()
        return tuple(a + b for a, b in zip(own, parent))


class UISkinEntry:
    def __init__(self, selector, config):
        self.__dict__['_selector'] = selector
        self.__dict__['_config'] = config

    def applicable(self, element, state):
        return self._selector.applicable(element, state)

    def specificity(self) -> tuple[int, int, int]:
        return self._selector.specificity()

    def update(self, other):
        self._config.update(other._config)

    def __getattr__(self, attr):
        return self._config.get(attr)

    def __setattr__(self, attr, value):
        if value is not None:
            self._config[attr] = value

    def resolved_font_size(self, element, skin):
        """The font size of the given element, in pixels, scaled by the global UI scale factor."""
        if self.font_size is None:
            # No font size sepecified at all,fall back to the skin's root font size.
            return skin.root_font_size * settings.ui_scale
        return self.font_size(element, skin)

    def resolved_size(self, element, skin, default=None):
        """
        Return the `width` and `height` of the given element, in pixels, scaled by the global UI scale factor.

        Args:
            element: the element the style has been collected for
            skin: the skin the style has been collected from
            default: value used for a dimension the skin does not set. When None, the element's
                font size is used.

        Returns:
            Tuple of (width, height)
        """
        if default is None:
            default = self.resolved_font_size(element, skin)
        width = self.width(element, skin) if self.width is not None else default
        height = self.height(element, skin) if self.height is not None else default
        return (width, height)

    def get_length(self, name: str, element: UIElement, skin: UISkin, default: float = 0.0) -> float:
        """
        Resolve a length property of this style into pixels.

        Args:
            name: Name of the property, e.g. 'border_width'
            element: The element this style was resolved for
            skin: The skin this style comes from
            default: Value to return when the property is unset

        Returns:
            The length in pixels
        """
        return resolve_length(getattr(self, name), element, skin, default)

    def get_edge_lengths(self, name: str, element: UIElement, skin: UISkin) -> Tuple[float, float, float, float]:
        """
        Resolve an edge-lengths property of this style into pixels.

        Args:
            name: Name of the property, e.g. 'margin'
            element: The element this style was resolved for
            skin: The skin this style comes from

        Returns:
            The four edge lengths in pixels, in DirectGUI order (left, right, bottom, top)
        """
        return resolve_edge_lengths(getattr(self, name), element, skin)

    def get_gap(self, element: UIElement, skin: UISkin) -> Tuple[float, float]:
        """
        Resolve the `gap` property of this style into pixels.

        Args:
            element: The element this style was resolved for
            skin: The skin this style comes from

        Returns:
            The (column, row) gaps in pixels, in the order expected by the sizer
        """
        return resolve_gap(self.gap, element, skin)

    def add_text_align(self, parameters: dict, key: str = 'text_align') -> None:
        """
        Add the `text-align` property, when the skin sets one, to a DirectGUI parameters dict.

        The property is left out when unset so that the widget's own default, or an explicit value
        passed by its creator, is used instead.

        Args:
            parameters: The DirectGUI parameters being built
            key: Name of the DirectGUI parameter to fill in
        """
        if self.text_align is not None:
            parameters[key] = self.text_align

    def get_font_parameters(self, element, skin, prefix=None, skip_scale=False, scale3=False, ui_scale=None):
        font_family = self.font_family
        font_style = Font.STYLE_NORMAL
        if self.font_style == 'italic':
            font_style |= Font.STYLE_ITALIC
        if self.font_weight == 'bold':
            font_style |= Font.STYLE_BOLD
        parameters = {
            'font': fontsManager.load_font(font_family, font_style),
        }
        if not skip_scale:
            font_size = self.resolved_font_size(element, skin)
            if ui_scale is None:
                ui_scale = (1, 1)
            if scale3:
                scale = (ui_scale[0] * font_size, 1, ui_scale[1] * font_size)
            else:
                scale = (ui_scale[0] * font_size, ui_scale[1] * font_size)
            parameters['scale'] = scale
        if prefix is not None:
            parameters = {(prefix + key): value for (key, value) in parameters.items()}
        return parameters

    def get_scale_from_width_height(self, element, skin, prefix=None, scale3=False):
        width, height = self.resolved_size(element, skin)
        if scale3:
            scale = (width, 1, height)
        else:
            scale = (width, height)
        parameters = {
            'scale': scale,
        }
        if prefix is not None:
            parameters = {(prefix + key): value for (key, value) in parameters.items()}
        return parameters

    def resolve_button_color(self, element, skin, prop, extra_state=None):
        """
        Resolve skin entry `prop` for the four visual states of DirectButton,
        returning a [ready, press, rollover, disabled] list.

        Args:
            element: the element the style has been collected for
            skin: the global skin configuration
            prop: name of the UISkinEntry property to resolve (e.g., 'background_color')
            extra_state: extra state to combine with the DirectButton visual states.
        """
        base_states = normalize_classes(extra_state) or frozenset()
        ready = getattr(self, prop)
        press = getattr(skin.get(element, base_states | {'active'}), prop)
        rollover = getattr(skin.get(element, base_states | {'hover'}), prop)
        disabled = getattr(skin.get(element, base_states | {'disabled'}), prop)
        return [
            ready,
            press if press is not None else ready,
            rollover if rollover is not None else ready,
            disabled if disabled is not None else ready,
        ]

    def get_dgui_parameters_for(
        self, element, prefix=None, skin=None, skip_font=False, usage=None, dgui=None, ui_scale=None, state=None
    ):
        dgui_type = dgui or element.type_
        font_size = self.resolved_font_size(element, skin)
        if dgui_type == 'button':
            parameters = {
                'frameColor': self.resolve_button_color(element, skin, 'background_color', extra_state=state),
                'text_fg': self.text_color,
                **(self.get_font_parameters(element, skin, 'text_') if not skip_font else {}),
            }
            self.add_text_align(parameters)
        elif dgui_type == 'borders':
            parameters = {
                'background_color': self.background_color,
                'border_color': self.border_color,
            }
        elif dgui_type == 'check-button':
            parameters = {
                'frameColor': self.resolve_button_color(element, skin, 'background_color', extra_state=state),
            }
            button = UIElement(parent=element, type_='button', class_='indicator')
            parameters.update(skin.get_style(button, prefix='indicator_'))
        elif dgui_type == 'entry':
            parameters = {
                'text_fg': self.text_color,
                'frameColor': self.background_color,
                **(self.get_font_parameters(element, skin, 'text_') if not skip_font else {}),
            }
            self.add_text_align(parameters)
        elif dgui_type == 'frame':
            parameters = {'frameColor': self.background_color}
        elif dgui_type == 'label':
            parameters = {
                'frameColor': self.background_color,
                'text_fg': self.text_color,
                **(self.get_font_parameters(element, skin, 'text_') if not skip_font else {}),
            }
            self.add_text_align(parameters)
        elif dgui_type == 'menu':
            hover = skin.get(element, 'hover')
            active = skin.get(element, 'active')
            disabled = skin.get(element, 'disabled')
            parameters = {
                'BGColor': self.background_color,
                # 'BGBorderColor': (0.3, 0.3, 0.3, 1),
                # 'separatorColor': (0, 0, 0, 1),
                'frameColorHover': hover.background_color,
                'frameColorPress': active.background_color,
                'textColorReady': self.text_color,
                'textColorHover': hover.text_color,
                'textColorPress': active.text_color,
                'textColorDisabled': disabled.text_color,
                **(self.get_font_parameters(element, skin, scale3=True, ui_scale=ui_scale) if not skip_font else {}),
            }
        elif dgui_type == 'onscreen-text':
            # `text-align` is deliberately not applied here: the alignment of an on-screen text is
            # dictated by the screen corner it is anchored to, not by the skin.
            parameters = {
                'fg': self.text_color,
                **(self.get_font_parameters(element, skin) if not skip_font else {}),
            }
        elif dgui_type == 'option-menu':
            hover = skin.get(element, 'hover')
            parameters = {
                'frameColor': self.resolve_button_color(element, skin, 'background_color', extra_state=state),
                'text_fg': self.text_color,
                # Item entries in the popup list share the closed menu's base colors; 'highlightColor' is
                # DirectOptionMenu's own hover tint for whichever item is under the mouse.
                'item_frameColor': self.background_color,
                'item_text_fg': self.text_color,
                'highlightColor': hover.background_color,
                'scale': (font_size, 1, font_size),
                'popupMenu_frameColor': self.background_color,
                **(self.get_font_parameters(element, skin, 'text_', skip_scale=True) if not skip_font else {}),
                **(self.get_font_parameters(element, skin, 'item_text_', skip_scale=True) if not skip_font else {}),
            }
            self.add_text_align(parameters)
            self.add_text_align(parameters, 'item_text_align')
        elif dgui_type == 'scroll-bar':
            parameters = {'frameColor': self.background_color}
            thumb = UIElement(parent=element, type_='button', class_='thumb')
            parameters.update(skin.get_style(thumb, prefix='thumb_'))
            inc_button = UIElement(parent=element, type_='button', class_='inc-button')
            parameters.update(skin.get_style(inc_button, prefix='incButton_'))
            dec_button = UIElement(parent=element, type_='button', class_='dec-button')
            parameters.update(skin.get_style(dec_button, prefix='decButton_'))
        elif dgui_type == 'scrolled-frame':
            parameters = {
                'frameColor': self.background_color,
                'scrollBarWidth': self.width(element, skin) if self.width is not None else font_size,
            }
            horizontal_scroll = UIElement(parent=element, type_='scroll-bar', class_='horizontal-scroll')
            parameters.update(skin.get_style(horizontal_scroll, prefix='horizontalScroll_'))
            vertical_scroll = UIElement(parent=element, type_='scroll-bar', class_='vertical-scroll')
            parameters.update(skin.get_style(vertical_scroll, prefix='verticalScroll_'))
        elif dgui_type == 'sizer':
            # A sizer has two sets of layout parameters: the ones of the sizer itself, and the ones
            # of the cell holding an object added to it. `usage` selects which of the two is built.
            if usage == 'cell':
                # The cell borders are the margin reserved around the object placed in that cell.
                parameters = {
                    'borders': self.get_edge_lengths('margin', element, skin),
                }
            else:
                parameters = {
                    'gaps': self.get_gap(element, skin),
                }
        elif dgui_type == 'spin-box':
            parameters = {
                'frameColor': self.background_color,
                'scale': (font_size, 1, font_size),
            }
            entry = UIElement(parent=element, type_='entry', class_='value-entry')
            parameters.update(skin.get_style(entry, 'valueEntry_'))
            inc_button = UIElement(parent=element, type_='button', class_='inc-button')
            parameters.update(skin.get_style(inc_button, prefix='incButton_', skip_font=True))
            dec_button = UIElement(parent=element, type_='button', class_='dec-button')
            parameters.update(skin.get_style(dec_button, prefix='decButton_', skip_font=True))
        elif dgui_type == 'slider':
            parameters = {
                'frameColor': self.text_color,
                **self.get_scale_from_width_height(element, skin, scale3=True),
            }
            thumb = UIElement(parent=element, type_='button', class_='thumb')
            parameters.update(skin.get_style(thumb, prefix='thumb_'))
        elif dgui_type == 'tabbed-frame':
            # A tab style with no state is its "unselected" look, overridden by
            # `selected` for the current tab and `disabled` for the inactive tab,
            # mirroring plain button  style.
            hover = skin.get(element, 'hover')
            active = skin.get(element, 'active')
            disabled = skin.get(element, 'disabled')
            selected = skin.get(element, 'selected')
            parameters = {
                'frameColor': self.background_color,
                #'scroll_frameColor': self.background_color,
                'tabSelectedColor': selected.background_color,
                'tabUnselectedColor': self.background_color,
                'tabInactiveColor': disabled.background_color,
                'tabRolloverOffsetColor': LColor(hover.background_color.xyz - self.background_color.xyz, 0.0),
                'tabClickOffsetColor': LColor(active.background_color.xyz - self.background_color.xyz, 0.0),
                'tab_scale': (font_size, 1, font_size),
                'tab_text_fg': self.text_color,
            }
            scrolled_frame = UIElement(parent=element, type_='scrolled-frame')
            parameters.update(skin.get_style(scrolled_frame, prefix='scroll_', skip_font=True))
        elif dgui_type == 'text':
            parameters = {
                'fg': self.text_color,
                **(self.get_font_parameters(element, skin) if not skip_font else {}),
            }
        else:
            classes = sorted(element.class_) if element.class_ else None
            report_error(
                f"Unknown widget type '{dgui_type}'",
                context=f"element type={element.type_!r} class={classes!r} id={element.id_!r}",
            )
            parameters = {}
        if prefix is not None:
            parameters = {(prefix + key): value for (key, value) in parameters.items()}
        return parameters


class UISkin:
    # Default root font size (in logical px, before ui_scale), matching the common browser default
    DEFAULT_ROOT_FONT_SIZE = 16.0

    def __init__(self):
        self.entries = []
        self.root_font_size = self.DEFAULT_ROOT_FONT_SIZE

    def add_entry(self, entry: UISkinEntry) -> None:
        self.entries.append(entry)

    def get(self, element: UIElement, state: Optional[Union[str, list[str]]] = None) -> UISkinEntry:
        """
        Resolve the style for `element`, restricted to entries whose state selector matches the given `state`.

        Args:
            element: the UIElement to resolve the style for
            state: a pseudo-class or iterable of pseudo-classes, or None for no state.
        Returns:
            A UISkinEntry with the resolved style for the element in the given state.
        """
        return self.collect_entries_for(element, state)

    def get_style(
        self,
        element: UIElement,
        state: Optional[Union[str, list[str]]] = None,
        prefix: Optional[str] = None,
        skip_font: bool = False,
        usage=None,
        dgui=None,
        ui_scale=None,
    ):
        style = self.collect_entries_for(element, state)
        return style.get_dgui_parameters_for(
            element,
            skin=self,
            prefix=prefix,
            skip_font=skip_font,
            usage=usage,
            dgui=dgui,
            ui_scale=ui_scale,
            state=state,
        )

    def collect_entries_for(self, element: UIElement, state: Optional[Union[str, list[str]]] = None) -> UISkinEntry:
        result = UISkinEntry(None, {})
        matching = [entry for entry in self.entries if entry.applicable(element, state)]
        # Stable sort: entries with equal specificity keep their declaration order, so the
        # last-declared one wins among ties, matching CSS specificity-then-source-order rule.
        matching.sort(key=lambda entry: entry.specificity())
        for entry in matching:
            result.update(entry)
        self._apply_inheritance(result, element)
        return result

    def _apply_inheritance(self, result: UISkinEntry, element: UIElement) -> None:
        """
        Fill in unset inheritable properties from the nearest ancestor that sets them.
        """
        if element.parent is None:
            return
        missing = [prop for prop in INHERITED_PROPERTIES if result._config.get(prop) is None]
        if not missing:
            return
        # Inheritance uses the parent's own computed style (state-independent)
        parent_style = self.collect_entries_for(element.parent, None)
        for prop in missing:
            value = getattr(parent_style, prop)
            if value is not None:
                setattr(result, prop, value)
