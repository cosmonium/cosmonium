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

from pandamenu.menu import DropDownMenu

from ..core.ui_element import DockedUIElement
from ..skin import UIElement


class Menubar(DockedUIElement):

    def __init__(self, menu_items, scale, parent=None):
        DockedUIElement.__init__(self, 'menubar', 'top', parent=parent)
        self.menu_items = menu_items
        self.scale = scale
        self.menubar = None

    def create(self):
        menubar_element = UIElement('menu', id_="menubar")
        style = self.skin.get_style(menubar_element, ui_scale=self.scale)
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
            **style,
        )

    def update_instance(self):
        # Nothing to update
        pass

    def show(self):
        self.menubar.menu.unstash()

    def hide(self):
        self.menubar.menu.stash()

    def get_height(self):
        return self.menubar.height
