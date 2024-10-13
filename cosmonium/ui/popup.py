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

from pandamenu.menu import PopupMenu

from .skin import UIElement


class Popup:

    def __init__(self, engine, menu_builder, owner):
        self.engine = engine
        self.menu_builder = menu_builder
        self.popup_done = None
        self.owner = owner
        if owner is not None:
            self.skin = owner.skin
        else:
            self.skin = None

    def create(self, scale, over, popup_done=None):
        self.popup_done = popup_done
        # TODO: This should not be done here !
        if over is not None:
            self.engine.select_body(over)
        items = self.menu_builder()
        popup_element = UIElement('menu', id_="popup")
        style = self.skin.get_style(popup_element, ui_scale=scale)
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
            **style
        )

    def on_destroy(self):
        if self.popup_done is not None:
            self.popup_done()
