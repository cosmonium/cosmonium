# -*- coding: utf-8 -*-
#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
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
from typing import FrozenSet, Iterable, Optional, Union

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
INHERITED_PROPERTIES = ('text_color', 'font_family', 'font_size', 'font_style', 'font_weight')


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
        self.state = state
        self.class_ = normalize_classes(class_)
        self.id_ = id_

    def applicable(self, element, state):
        return (
            (self.type_ is None or self.type_ == element.type_)
            and (self.state is None or self.state == state)
            and (self.class_ is None or self.class_.issubset(element.class_ or frozenset()))
            and (self.id_ is None or self.id_ == element.id_)
        )

    def specificity(self) -> tuple[int, int, int]:
        """
        CSS-like specificity as an (id, class-or-state, type) tuple, higher wins.

        Mirrors CSS (id, class/attribute/pseudo-class, type) ordering: an id
        match outweighs any number of class/state matches, which in turn
        outweigh a type match. A compound class selector (multiple required
        classes) contributes one point per class.
        """
        class_count = len(self.class_) if self.class_ else 0
        return (
            1 if self.id_ is not None else 0,
            class_count + (1 if self.state is not None else 0),
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

    def calc_size_em(self, size, element, font_size, skin):
        if font_size:
            return skin.get(element.parent).font_size(element.parent, False, skin) * size
        else:
            return skin.get(element).font_size(element, False, skin) * size

    def calc_size_px(self, size, element, font_size, skin):
        return size * settings.ui_scale

    def calc_size_rem(self, size, element, font_size, skin):
        return skin.root_font_size * settings.ui_scale * size

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
            font_size = self.font_size(element, True, skin)
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
        font_size = self.font_size(element, False, skin)
        if self.width is not None:
            width = self.width(element, False, skin)
        else:
            width = font_size
        if self.height is not None:
            height = self.height(element, False, skin)
        else:
            height = font_size
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

    def get_dgui_parameters_for(
        self, element, prefix=None, skin=None, skip_font=False, usage=None, dgui=None, ui_scale=None
    ):
        dgui_type = dgui or element.type_
        font_size = self.font_size(element, True, skin)
        if dgui_type == 'button':
            parameters = {
                'frameColor': self.background_color,
                'text_fg': self.text_color,
                **(self.get_font_parameters(element, skin, 'text_') if not skip_font else {}),
            }
        elif dgui_type == 'borders':
            parameters = {
                'background_color': self.background_color,
                'border_color': self.border_color,
            }
        elif dgui_type == 'check-button':
            parameters = {
                'frameColor': self.background_color,
            }
            button = UIElement(parent=element, type_='button', class_='indicator')
            parameters.update(skin.get_style(button, prefix='indicator_'))
        elif dgui_type == 'entry':
            parameters = {
                'text_fg': self.text_color,
                'frameColor': self.background_color,
                **(self.get_font_parameters(element, skin, 'text_') if not skip_font else {}),
            }
        elif dgui_type == 'frame':
            parameters = {'frameColor': self.background_color}
        elif dgui_type == 'label':
            parameters = {
                'frameColor': self.background_color,
                'text_fg': self.text_color,
                **(self.get_font_parameters(element, skin, 'text_') if not skip_font else {}),
            }
        elif dgui_type == 'menu':
            hover = skin.get(element, 'hover')
            clicked = skin.get(element, 'clicked')
            disabled = skin.get(element, 'disabled')
            parameters = {
                'BGColor': self.background_color,
                # 'BGBorderColor': (0.3, 0.3, 0.3, 1),
                # 'separatorColor': (0, 0, 0, 1),
                'frameColorHover': hover.background_color,
                'frameColorPress': clicked.background_color,
                'textColorReady': self.text_color,
                'textColorHover': hover.text_color,
                'textColorPress': clicked.text_color,
                'textColorDisabled': disabled.text_color,
                **(self.get_font_parameters(element, skin, scale3=True, ui_scale=ui_scale) if not skip_font else {}),
            }
        elif dgui_type == 'onscreen-text':
            parameters = {
                'fg': self.text_color,
                **(self.get_font_parameters(element, skin) if not skip_font else {}),
            }
        elif dgui_type == 'option-menu':
            hover = skin.get(element, 'hover')
            parameters = {
                'frameColor': self.background_color,
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
                'scrollBarWidth': self.width(element, False, skin) if self.width else font_size,
            }
            horizontal_scroll = UIElement(parent=element, type_='scroll-bar', class_='horizontal-scroll')
            parameters.update(skin.get_style(horizontal_scroll, prefix='horizontalScroll_'))
            vertical_scroll = UIElement(parent=element, type_='scroll-bar', class_='vertical-scroll')
            parameters.update(skin.get_style(vertical_scroll, prefix='verticalScroll_'))
        elif dgui_type == 'sizer':
            if usage == 'cell':
                if self.padding is not None:
                    borders = [padding(element, False, skin) for padding in self.padding]
                else:
                    borders = None
                parameters = {
                    'borders': borders,
                }
            else:
                if self.margin is not None:
                    gaps = [margin(element, False, skin) for margin in (self.margin[0], self.margin[2])]
                else:
                    gaps = (0, 0)
                parameters = {
                    'gaps': gaps,
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
            hover = skin.get(element, 'hover')
            clicked = skin.get(element, 'clicked')
            inactive = skin.get(element, 'inactive')
            selected = skin.get(element, 'selected')
            unselected = skin.get(element, 'unselected')
            parameters = {
                'frameColor': self.background_color,
                #'scroll_frameColor': self.background_color,
                'tabSelectedColor': selected.background_color,
                'tabUnselectedColor': unselected.background_color,
                'tabInactiveColor': inactive.background_color,
                'tabRolloverOffsetColor': LColor(hover.background_color.xyz - unselected.background_color.xyz, 0.0),
                'tabClickOffsetColor': LColor(clicked.background_color.xyz - unselected.background_color.xyz, 0.0),
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

    def add_entry(self, entry):
        self.entries.append(entry)

    def get(self, element, state=None):
        return self.collect_entries_for(element, state)

    def get_style(self, element, state=None, prefix=None, skip_font=False, usage=None, dgui=None, ui_scale=None):
        style = self.collect_entries_for(element, state)
        return style.get_dgui_parameters_for(
            element, skin=self, prefix=prefix, skip_font=skip_font, usage=usage, dgui=dgui, ui_scale=ui_scale
        )

    def collect_entries_for(self, element, state):
        result = UISkinEntry(None, {})
        matching = [entry for entry in self.entries if entry.applicable(element, state)]
        # Stable sort: entries with equal specificity keep their declaration order, so the
        # last-declared one wins among ties, matching CSS specificity-then-source-order rule.
        matching.sort(key=lambda entry: entry.specificity())
        for entry in matching:
            result.update(entry)
        self._apply_inheritance(result, element)
        return result

    def _apply_inheritance(self, result, element):
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
