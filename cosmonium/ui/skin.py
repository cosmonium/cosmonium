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

from dataclasses import dataclass
from panda3d.core import LColor
from typing import Optional

from ..fonts import fontsManager, Font
from .. import settings


@dataclass
class UIElement:
    type_: str
    parent: Optional[UIElement] = None
    class_: Optional[str] = None
    id_: Optional[str] = None


class Selector:
    def __init__(self, type_, state, class_, id_):
        self.type_ = type_
        self.state = state
        self.class_ = class_
        self.id_ = id_

    def applicable(self, element, state):
        return (
            (self.type_ is None or self.type_ == element.type_)
            and (self.state is None or self.state == state)
            and (self.class_ is None or self.class_ == element.class_)
            and (self.id_ is None or self.id_ == element.id_)
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


class UISkinEntry:
    def __init__(self, selector, config):
        self.__dict__['_selector'] = selector
        self.__dict__['_config'] = config

    def applicable(self, element, state):
        return self._selector.applicable(element, state)

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

    def get_font_parameters(self, element, skin, prefix=None, scale3=False):
        font_family = self.font_family
        font_style = Font.STYLE_NORMAL
        if self.font_style == 'italic':
            font_style = Font.STYLE_ITALIC
        if self.font_weight == 'bold':
            font_style = Font.STYLE_BOLD
        font_size = self.font_size(element, True, skin)
        if scale3:
            scale = (font_size, 1, font_size)
        else:
            scale = (font_size, font_size)
        parameters = {
            'scale': scale,
            'font': fontsManager.load_font(font_family, font_style),
        }
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

    def get_dgui_parameters_for(self, element, prefix=None, skin=None, skip_font=False, usage=None, dgui=None):
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
        elif dgui_type == 'onscreen-text':
            parameters = {
                'fg': self.text_color,
                **(self.get_font_parameters(element, skin) if not skip_font else {}),
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
            print("Unknown widget", dgui_type)
            parameters = {}
        if prefix is not None:
            parameters = {(prefix + key): value for (key, value) in parameters.items()}
        return parameters


class UISkin:
    def __init__(self):
        self.entries = []

    def add_entry(self, entry):
        self.entries.append(entry)

    def get(self, element, state=None):
        return self.collect_entries_for(element, state)

    def get_style(self, element, state=None, prefix=None, skip_font=False, usage=None, dgui=None):
        style = self.collect_entries_for(element, state)
        return style.get_dgui_parameters_for(
            element, skin=self, prefix=prefix, skip_font=skip_font, usage=usage, dgui=dgui
        )

    def collect_entries_for(self, element, state):
        result = UISkinEntry(None, {})
        for entry in self.entries:
            if entry.applicable(element, state):
                result.update(entry)
        return result
