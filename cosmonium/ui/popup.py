#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2021 Laurent Deru.
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

from ..extrainfo import extra_info
from .. import settings

from .menucommon import create_orbiting_bodies_menu_items, create_orbits_menu_items, create_surfaces_menu_items

class Popup:
    def __init__(self, gui, messenger, engine, browser):
        self.gui = gui
        self.messenger = messenger
        self.engine = engine
        self.browser = browser
        self.popup_done = None

    def menu_text(self, text, state, event, condition=None, args=[]):
        if condition is not None:
            event = event if condition else 0
        return (text, state, self.messenger.send, event, args)

    def create_main_popup(self, over):
        items = []
        if over is not None:
            self.engine.select_body(over)
            items.append(self.menu_text(over.get_friendly_name(), 0, 'center-selected'))
            items.append(0)
            items.append(self.menu_text(_('_Info'), 0, 'gui-show-info'))
            items.append(self.menu_text(_('_Goto'), 0, 'goto-selected'))
            items.append(self.menu_text(_('_Follow'), 0, 'follow-selected'))
            items.append(self.menu_text(_('S_ync'), 0, 'sync-selected'))
            subitems = create_surfaces_menu_items(over)
            items.append([_("Surfaces"), 0, subitems])
            subitems = create_orbiting_bodies_menu_items(self.engine, over)
            if len(subitems) > 0:
                items.append([_("Orbiting bodies"), 0, subitems])
            subitems = create_orbits_menu_items(self.engine, over)
            if len(subitems) > 0:
                items.append([_("Orbits"), 0, subitems])
            items.append(self.menu_text(_('_Edit'), 0, 'gui-show-editor'))
            subitems = []
            #TODO: Should be moved to menucommon and use events
            for info in extra_info:
                name = info.get_name()
                url = info.get_url_for(over)
                if url is not None:
                    subitems.append([name, 0, self.browser.load, url])
            if len(subitems) > 0:
                items.append([_("More info"), 0, subitems])
        if not self.gui.menubar_shown:
            if over is not None:
                items.append(0)
            items.append(self.menu_text(_('Show _menubar'), 0, self.gui.show_menu))
        return items

    def create(self, font, scale, over, popup_done=None):
        self.popup_done = popup_done
        items = self.create_main_popup(over)
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
