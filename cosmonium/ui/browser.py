#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2019 Laurent Deru.
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

from __future__ import print_function
from __future__ import absolute_import

from .window import Window

from cefpanda import cefpanda

class Browser(object):
    def __init__(self, scale, owner=None):
        self.scale = scale
        self.owner = owner
        self.window = None
        self.renderer = None
        self.last_pos = None

    def create_renderer(self):
        if self .renderer is None:
            self.layout = cefpanda.CefDirectFrameTarget(self.scale, 600, 800)
            self.renderer = cefpanda.CEFPanda(self.layout)
            self.renderer.use_mouse = False
        self.layout.create()
        self.window = Window("Browser", scale=self.scale, child=None, owner=self, transparent=False)

    def load(self, url):
        self.show()
        self.renderer.load_url(url)
        self.renderer.use_mouse = True

    def show(self):
        if self.shown():
            return
        self.create_renderer()
        self.window.set_child(self.layout)
        if self.last_pos is None:
            self.last_pos = (-self.layout.frame['frameSize'][1] / 2, 0, -self.layout.frame['frameSize'][3] / 2)
        self.window.setPos(self.last_pos)
        self.window.update()

    def hide(self):
        if self.window is not None:
            self.last_pos = self.window.getPos()
            self.window.destroy()
            self.renderer.load_url("about:blank")
            self.renderer.use_mouse = False
            self.layout.destroy()
            self.window = None

    def shown(self):
        return self.window is not None

    def window_closed(self, window):
        if window is self.window:
            self.renderer.load_url("about:blank")
            self.renderer.use_mouse = False
            self.layout.destroy()
            self.last_pos = self.window.getPos()
            self.window = None
            if self.owner is not None:
                self.owner.window_closed(self)
