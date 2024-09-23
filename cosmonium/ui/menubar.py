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

from panda3d.core import LVector3
from pandamenu.menu import DropDownMenu

from .. import settings


class Menubar:

    def __init__(self, menu_items):
        self.menu_items = menu_items
        self.menubar = None

    def create(self, font, scale):
        scale = LVector3(scale[0], 1.0, scale[1])
        scale[0] *= settings.menu_text_size
        scale[2] *= settings.menu_text_size
        self.menubar = DropDownMenu(
            items=self.menu_items,
            font=font,
            sidePad=0.75,
            align=DropDownMenu.ALeft,
            baselineOffset=-0.35,
            scale=scale,
            itemHeight=1.2,
            leftPad=0.2,
            separatorHeight=0.3,
            underscoreThickness=1,
            BGColor=(0.9, 0.9, 0.9, 0.9),
            BGBorderColor=(0.3, 0.3, 0.3, 1),
            separatorColor=(0, 0, 0, 1),
            frameColorHover=(0.3, 0.3, 0.3, 1),
            frameColorPress=(0.3, 0.3, 0.3, 0.1),
            textColorReady=(0, 0, 0, 1),
            textColorHover=(0.7, 0.7, 0.7, 1),
            textColorPress=(0, 0, 0, 1),
            textColorDisabled=(0.3, 0.3, 0.3, 1),
        )

    def show(self):
        self.menubar.menu.unstash()

    def hide(self):
        self.menubar.menu.stash()

    def get_height(self):
        return self.menubar.height
