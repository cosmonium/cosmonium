#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2022 Laurent Deru.
#
#Cosmonium is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Cosmonium is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#

from panda3d.core import LVector3
from pandamenu.menu import PopupMenu

from .. import settings

class Popup:
    def __init__(self, gui, engine, menu_items):
        self.gui = gui
        self.engine = engine
        self.menu_items = menu_items
        self.popup_done = None

    def create(self, font, scale, over, popup_done=None):
        self.popup_done = popup_done
        items = self.menu_items()
        # TODO: This should not be done here !
        if over is not None:
            self.engine.select_body(over)
        if not self.gui.menubar_shown:
            if over is not None:
                items.append(0)
            items.append(self.menu_text(_('Show _menubar'), 0, self.gui.show_menu))
        scale = LVector3(scale[0], 1.0, scale[1])
        scale[0] *= settings.menu_text_size
        scale[2] *= settings.menu_text_size
        PopupMenu(items=items,
                  font=font,
                  baselineOffset=-.35,
                  scale=scale, itemHeight=1.2, leftPad=.2,
                  separatorHeight=.3,
                  underscoreThickness=1,
                  BGColor=(.9,.9,.9,.9),
                  BGBorderColor=(.3,.3,.3,1),
                  separatorColor=(0,0,0,1),
                  frameColorHover=(.3,.3,.3,1),
                  frameColorPress=(.3,.3,.3,.1),
                  textColorReady=(0,0,0,1),
                  textColorHover=(.7,.7,.7,1),
                  textColorPress=(0,0,0,1),
                  textColorDisabled=(.3,.3,.3,1),
                  onDestroy=self.on_destroy
                  )

    def on_destroy(self):
        if self.popup_done is not None:
            self.popup_done()
