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


from abc import abstractmethod
from panda3d.core import LVector2

from ... import settings
from ..core.ui_element import FloatingUIElement
from ..widgets.window_frame import WindowFrame


class UIWindow(FloatingUIElement):
    """Base class for all window types."""

    def __init__(self, parent=None):
        super().__init__(id_='window', parent=parent)
        self.window = None
        self.layout = None
        self.last_pos = None
        if parent is not None:
            self.anchor = parent.anchor
        else:
            self.anchor = None
        self.scale = LVector2(settings.ui_scale, settings.ui_scale)

    def set_parent(self, parent):
        FloatingUIElement.set_parent(self, parent)
        if parent is not None:
            self.anchor = parent.anchor

    def get_ui(self):
        return self.parent.get_ui() if self.parent else None

    def set_limits(self, limits):
        if self.window is not None:
            self.window.set_limits(limits)

    @abstractmethod
    def create_layout(self, *args, **kwargs):
        """Create the window layout."""
        ...

    def create(self):
        """Create the UI element."""
        # TODO: Refactor window frame creation here
        self.create_layout()

    def create_window_frame(self, title):
        return WindowFrame(title, scale=self.scale, child=self.layout, parent=self)

    def show(self):
        if self.shown():
            print("Window already shown")
            return
        self.create_layout()
        if self.last_pos is None:
            if self.layout is not None and self.parent is not None:
                width = self.layout.frame['frameSize'][1] - self.layout.frame['frameSize'][0]
                height = self.layout.frame['frameSize'][3] - self.layout.frame['frameSize'][2]
                self.last_pos = ((self.parent.width - width) / 2, 0, -(self.parent.height - height) / 2)
            else:
                self.last_pos = (100, 0, -100)
        self.window.setPos(self.last_pos)
        self.window.update()

    def hide(self):
        if self.window is not None:
            self.destroy()

    def shown(self):
        return self.window is not None

    def destroy(self):
        super().destroy()
        if self.window is not None:
            self.last_pos = self.window.getPos()
            self.window.destroy()
            self.window = None
        if self.layout is not None:
            self.layout.destroy()
            self.layout = None
        if self.parent is not None:
            self.parent.window_closed(self)

    def window_closed(self):
        self.destroy()

    def update_instance(self):
        """Update the visual instance."""
        if self.window is not None:
            self.window.update()
