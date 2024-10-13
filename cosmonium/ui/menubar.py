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

from pandamenu.menu import DropDownMenu

from .skin import UIElement


class Menubar:

    def __init__(self, menu_items, owner):
        self.menu_items = menu_items
        self.menubar = None
        self.owner = owner
        if owner is not None:
            self.skin = owner.skin
        else:
            self.skin = None

    def create(self, scale):
        menubar_element = UIElement('menu', id_="menubar")
        style = self.skin.get_style(menubar_element, ui_scale=scale)
        self.menubar = DropDownMenu(
            items=self.menu_items,
            sidePad=0.75,
            align=DropDownMenu.ALeft,
            baselineOffset=-0.35,
            # scale=scale,
            itemHeight=1.2,
            leftPad=0.2,
            separatorHeight=0.3,
            underscoreThickness=1,
            BGBorderColor=(0.3, 0.3, 0.3, 1),
            separatorColor=(0, 0, 0, 1),
            **style
        )

    def show(self):
        self.menubar.menu.unstash()

    def hide(self):
        self.menubar.menu.stash()

    def get_height(self):
        return self.menubar.height
