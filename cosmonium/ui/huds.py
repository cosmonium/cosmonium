#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2024 Laurent Deru.
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


from dataclasses import dataclass
from itertools import chain
from panda3d.core import TextNode, LVector2

from .dock.dock import Dock
from .hud.fadetextline import FadeTextLine
from .skin import UIElement

from .jinja import JinjaEnv


@dataclass
class HudEntry:
    title: str
    text: str


class Huds():
    def __init__(self, gui, widgets, dock, skin):
        self.owner = gui
        self.skin = skin
        self.env = JinjaEnv(base)
        self.element = UIElement(None, class_='hud', id_='hud')
        self.widgets = widgets
        for anchor_name in self.widgets.keys():
            if anchor_name == 'top-left':
                anchor = base.p2dTopLeft
            elif anchor_name == 'top-right':
                anchor = base.p2dTopRight
            elif anchor_name == 'bottom-left':
                anchor = base.p2dBottomLeft
            elif anchor_name == 'bottom-right':
                anchor = base.p2dBottomRight
            for widget in self.widgets[anchor_name]:
                widget.set_owner(self)
                widget.set_anchor(anchor)
                widget.compile(self.env)
                widget.create()
        #TODO: Info should be moved out of HUD
        self.info = FadeTextLine('info', TextNode.ALeft, LVector2(0, -3), owner=self)
        self.info.set_anchor(base.p2dBottomLeft)
        self.info.create()
        # TODO: Temporary broken way to instanciate a dock
        if dock is not None:
            layout, orientation, location = dock
            self.bottom_dock = Dock(gui, base.pixel2d, orientation, location, layout, LVector2(1, 1), LVector2(0, 0), skin)
        else:
            self.bottom_dock = None
        self.shown = True

    def hide(self):
        for widget in chain(*self.widgets.values()):
            widget.hide()
        self.shown = False

    def show(self):
        for widget in chain(*self.widgets.values()):
            widget.show()
        self.shown = True

    def set_scale(self, scale):
        for widget in chain(*self.widgets.values()):
            widget.set_scale(scale)
        self.info.set_scale(scale)

    def set_y_offset(self, y_offset):
        for anchor_name, widgets in self.widgets.items():
            if not anchor_name.startswith('top'):
                continue
            offset = y_offset
            for widget in widgets:
                widget.set_offset((0, offset))
                offset += widget.get_height()

    def update(self, cosmonium, camera, mouse, nav, autopilot, time):
        for widget in chain(*self.widgets.values()):
            widget.update()
        if self.bottom_dock is not None:
            self.bottom_dock.update()

    def update_size(self):
        if self.bottom_dock is not None:
            self.bottom_dock.update_size()
