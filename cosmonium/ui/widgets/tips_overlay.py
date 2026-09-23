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

import builtins
from typing import TYPE_CHECKING, List

from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectButton import DirectButton
from direct.gui.DirectFrame import DirectFrame
from direct.gui.OnscreenText import OnscreenText, Plain
from panda3d.core import TextNode

from ..skin import UIElement, resolve_edge_lengths
from .decorated_frame import FrameDecoration

if TYPE_CHECKING:
    from ..config.models import TipConfig
    from ..gui import Gui


class TipsOverlay:
    """A small, non-modal popup showing the first-run tips one at a time.

    Docked to a screen cornern clear of the window edge and of any dock or menubar sharing that edge,
    with Back/Next navigation.

    Note: Follow the minimal interface `WindowManager` expects of a window, so it is tracked and
    closable (Escape) exactly like any other window.
    """

    # TODO: Should make it configurable through the skin or the config.
    # Clearance from the screen edge.
    MARGIN = 20
    # Extra clearance from a dock or menubar sharing the same edge.
    GAP = 12
    # Fixed content width; only the panel height varies with the current tip text.
    CONTENT_WIDTH = 280

    def __init__(self, gui: Gui, tips: List[TipConfig], corner: str = 'bottom-left'):
        self.gui = gui
        self.skin = gui.skin
        self.tips = tips
        self.corner = corner
        self.index = 0
        self.frame: DirectFrame = None
        self.title_text: OnscreenText = None
        self.body_text: OnscreenText = None
        self.counter_text: OnscreenText = None
        self._build()
        self._update_content()

    def _build(self) -> None:
        frame_element = UIElement('frame', class_='tips')
        self.decoration = FrameDecoration(frame_element, self.skin)
        self.padding = resolve_edge_lengths(self.skin.get(frame_element).padding, frame_element, self.skin)
        self.frame = DirectFrame(parent=builtins.base.pixel2d)

        self.title_element = UIElement('onscreen-text', id_='tips-title')
        self.body_element = UIElement('onscreen-text', id_='tips-body')
        self.body_style = self.skin.get_style(self.body_element)
        # `wordwrap` size is in the text's own pre-scale units, so convert the desired pixel width
        # using the font scale this style resolves to.
        self.wordwrap = self.CONTENT_WIDTH / self.body_style['scale'][0]
        self.counter_element = UIElement('onscreen-text', id_='tips-counter')

        nav_element = UIElement('button', class_=('tips', 'nav'))
        nav_style = self.skin.get_style(nav_element)
        self.back_button = DirectButton(
            parent=self.frame,
            text=_('Back'),
            text_align=TextNode.ACenter,
            relief=DGG.FLAT,
            command=self._on_back,
            **nav_style,
        )
        self.next_button = DirectButton(
            parent=self.frame,
            text=_('Next'),
            text_align=TextNode.ACenter,
            relief=DGG.FLAT,
            command=self._on_next,
            **nav_style,
        )

        close_frame_element = UIElement('frame', class_='close-frame')
        self.close_frame = DirectFrame(parent=self.frame, state=DGG.NORMAL, **self.skin.get_style(close_frame_element))
        close_text_element = UIElement('onscreen-text', class_='close-text')
        self.close_text = OnscreenText(
            parent=self.close_frame,
            text='x',
            style=Plain,
            align=TextNode.ACenter,
            pos=(0, 0),
            mayChange=True,
            **self.skin.get_style(close_text_element),
        )
        close_bounds = self.close_text.get_tight_bounds()
        close_size = max(close_bounds[1][0] - close_bounds[0][0], close_bounds[1][2] - close_bounds[0][2])
        close_pad = close_size * 0.4
        self.close_frame['frameSize'] = (
            -close_size / 2 - close_pad,
            close_size / 2 + close_pad,
            -close_size / 2 - close_pad,
            close_size / 2 + close_pad,
        )
        self.close_frame.bind(DGG.B1PRESS, self._on_close)

    def _on_next(self, *_args) -> None:
        if self.index < len(self.tips) - 1:
            self.index += 1
            self._update_content()
        else:
            self._on_close()

    def _on_back(self, *_args) -> None:
        if self.index > 0:
            self.index -= 1
            self._update_content()

    def _on_close(self, *_args) -> None:
        self.hide()

    def _create_text(self) -> None:
        """Create the title/body/counter text nodes for the current tip."""
        for text_node in (self.title_text, self.body_text, self.counter_text):
            if text_node is not None:
                text_node.destroy()

        tip = self.tips[self.index]
        self.title_text = OnscreenText(
            parent=self.frame,
            text=tip.title,
            style=Plain,
            align=TextNode.ALeft,
            **self.skin.get_style(self.title_element),
        )
        self.body_text = OnscreenText(
            parent=self.frame,
            text=tip.text,
            style=Plain,
            align=TextNode.ALeft,
            wordwrap=self.wordwrap,
            **self.body_style,
        )
        if len(self.tips) > 1:
            counter = _('{current} / {total}').format(current=self.index + 1, total=len(self.tips))
        else:
            counter = ''
        self.counter_text = OnscreenText(
            parent=self.frame,
            text=counter,
            style=Plain,
            align=TextNode.ALeft,
            **self.skin.get_style(self.counter_element),
        )

    def _update_content(self) -> None:
        self._create_text()
        is_last = self.index == len(self.tips) - 1
        self.next_button['text'] = _('Got it') if is_last else _('Next')
        # DirectButton doesn't auto-resize its frame when its text changes.
        self.next_button.resetFrameSize()
        if self.index == 0:
            self.back_button.hide()
        else:
            self.back_button.show()
        self._layout()
        self._position()

    def _layout(self) -> None:
        left, right, bottom, top = self.padding
        inset = self.decoration.content_inset
        left, right, bottom, top = left + inset, right + inset, bottom + inset, top + inset
        gap = 8

        y = -top
        title_bounds = self.title_text.get_tight_bounds()
        self.title_text.setPos(left - title_bounds[0][0], -top - title_bounds[1][2])
        y -= title_bounds[1][2] - title_bounds[0][2] + gap

        body_bounds = self.body_text.get_tight_bounds()
        self.body_text.setPos(left - body_bounds[0][0], y - body_bounds[1][2])
        y -= body_bounds[1][2] - body_bounds[0][2] + gap * 1.5

        next_bounds = self.next_button.getBounds()
        back_bounds = self.back_button.getBounds()
        row_height = max(next_bounds[3] - next_bounds[2], back_bounds[3] - back_bounds[2])
        content_width = self.CONTENT_WIDTH

        next_width = next_bounds[1] - next_bounds[0]
        next_x = left + content_width - next_width
        self.next_button.setPos(next_x - next_bounds[0], 0, y - row_height - next_bounds[2])

        if not self.back_button.is_hidden():
            back_width = back_bounds[1] - back_bounds[0]
            back_x = next_x - gap - back_width
            self.back_button.setPos(back_x - back_bounds[0], 0, y - row_height - back_bounds[2])

        counter_bounds = self.counter_text.get_tight_bounds()
        counter_height = counter_bounds[1][2] - counter_bounds[0][2]
        counter_y = y - (row_height + counter_height) / 2
        self.counter_text.setPos(left - counter_bounds[0][0], counter_y - counter_bounds[1][2])

        y -= row_height

        width = content_width + left + right
        height = -y + bottom
        self.panel_size = (width, height)
        self.frame['frameSize'] = (0, width, -height, 0)
        self.frame['frameColor'] = self.decoration.frame_color()
        self.frame['geom'] = self.decoration.build_geom(self.panel_size)
        self.close_frame.setPos(width - right / 2, 0, -top / 2)

    def _position(self) -> None:
        width, height = self.panel_size
        left_margin = self.MARGIN
        bottom_margin = self.MARGIN
        top_margin = self.MARGIN
        for dock in self.gui.dock_config or []:
            dock_height = dock.get_height()
            dock_width = dock.get_width()
            if dock.location.startswith('bottom'):
                bottom_margin = max(bottom_margin, self.MARGIN + dock_height + self.GAP)
            if dock.location.startswith('top'):
                top_margin = max(top_margin, self.MARGIN + dock_height + self.GAP)
            if dock.location.startswith('left'):
                left_margin = max(left_margin, self.MARGIN + dock_width + self.GAP)
        if self.gui.menubar_shown and self.gui.menubar is not None:
            top_margin = max(top_margin, self.MARGIN + self.gui.menubar.get_height() + self.GAP)

        if self.corner == 'top-left':
            x = left_margin
            z = -top_margin
        else:
            x = left_margin
            window_height = builtins.base.win.get_y_size()
            z = -(window_height - bottom_margin - height)
        self.frame.setPos(x, 0, z)

    def show(self) -> None:
        self.frame.show()

    def hide(self) -> None:
        if self.frame is not None:
            self.frame.destroy()
            self.frame = None
        self.gui.window_closed(self)

    def set_limits(self, limits) -> None:
        pass
