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

from pandamenu.menu import PopupMenu

from ..core.ui_element import UIElement
from ..skin import UIElement as SKinUIElement


class Popup(UIElement):

    def __init__(self, engine, scale, menu_builder, over, parent=None, popup_done=None):
        UIElement.__init__(self, 'popup', parent)
        self.engine = engine
        self.scale = scale
        self.menu_builder = menu_builder
        self.over = over
        self.popup_done = popup_done

    def create(self):
        # TODO: This should not be done here !
        if self.over is not None:
            self.engine.select_body(self.over)
        items = self.menu_builder()
        popup_element = SKinUIElement('menu', id_="popup")
        style = self.skin.get_style(popup_element, ui_scale=self.scale)
        PopupMenu(
            items=items,
            baselineOffset=-0.35,
            itemHeight=1.2,
            leftPad=0.2,
            separatorHeight=0.3,
            underscoreThickness=1,
            BGBorderColor=(0.3, 0.3, 0.3, 1),
            separatorColor=(0, 0, 0, 1),
            onDestroy=self.on_destroy,
            **style,
        )

    def update_instance(self):
        # Nothing to update
        pass

    def on_destroy(self):
        if self.popup_done is not None:
            self.popup_done()
