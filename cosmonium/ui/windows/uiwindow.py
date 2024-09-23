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


from panda3d.core import LVector2

from ... import settings


class UIWindow:
    def __init__(self, owner=None):
        self.window = None
        self.layout = None
        self.last_pos = None
        self.scale = LVector2(settings.ui_scale, settings.ui_scale)
        self.owner = owner
        self.skin = owner.skin

    def get_ui(self):
        return self.owner.get_ui()

    def set_limits(self, limits):
        if self.window is not None:
            self.window.set_limits(limits)

    def create_layout(self, *args, **kwargs):
        pass

    def show(self, *args, **kwargs):
        if self.shown():
            print("Window already shown")
            return
        self.create_layout(*args, **kwargs)
        if self.last_pos is None:
            if self.layout is not None and self.owner is not None:
                width = self.layout.frame['frameSize'][1] - self.layout.frame['frameSize'][0]
                height = self.layout.frame['frameSize'][3] - self.layout.frame['frameSize'][2]
                self.last_pos = ((self.owner.width - width) / 2, 0, -(self.owner.height - height) / 2)
            else:
                self.last_pos = (100, 0, -100)
        self.window.setPos(self.last_pos)
        self.window.update()

    def hide(self):
        if self.window is not None:
            self.last_pos = self.window.getPos()
            self.window.destroy()
            self.window = None
            self.layout = None

    def shown(self):
        return self.window is not None

    def window_closed(self, window):
        if window is self.window:
            self.last_pos = self.window.getPos()
            self.window = None
            self.layout = None
            if self.owner is not None:
                self.owner.window_closed(self)
