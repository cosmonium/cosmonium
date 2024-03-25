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


import traceback

from ... import settings
from ..widgets.window import Window
from .uiwindow import UIWindow

cefpanda_valid = False
try:
    import cefpanda
    cefpanda_valid = True
except Exception:
    print("ERROR: Could not load cefpanda")
    traceback.print_exc()


class Browser(UIWindow):
    def __init__(self, scale, owner=None):
        UIWindow.__init__(self, owner)
        self.renderer = None

    def create_layout(self):
        if self .renderer is None:
            self.layout = cefpanda.CefDirectFrameTarget((1, 1), 600, 800)
            self.renderer = cefpanda.CEFPanda(self.layout, settings.use_srgb)
            self.renderer.use_mouse = False
        self.layout.create()
        self.window = Window("Browser", scale=self.scale, child=self.layout, owner=self)

    def load(self, url):
        if not cefpanda_valid:
            print("CEFPanda not loaded, ignoring load url")
            return
        self.show()
        self.renderer.load_url(url)
        self.renderer.use_mouse = True

    def show(self):
        if not cefpanda_valid:
            return
        UIWindow.show(self)

    def hide(self):
        if self.window is not None:
            self.renderer.load_url("about:blank")
            self.renderer.use_mouse = False
            self.layout.destroy()
        UIWindow.hide(self)

    def window_closed(self, window):
        if window is self.window:
            self.renderer.load_url("about:blank")
            self.renderer.use_mouse = False
            self.layout.destroy()
        UIWindow.window_closed(self, window)
