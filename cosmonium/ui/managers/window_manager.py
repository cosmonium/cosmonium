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

"""Window lifecycle management."""


from __future__ import annotations


class WindowManager:
    """Manages window creation, opening, closing and lifecycle."""

    _instance: WindowManager

    def __init__(self, gui):
        """Initialize the window manager.

        Args:
            gui: The main GUI instance
        """
        self.gui = gui
        self.open_windows = []
        self.windows_by_id = {}

    @classmethod
    def register_instance(cls, instance):
        cls._instance = instance

    @classmethod
    def instance(cls):
        return cls._instance

    def open_window(self, window, id_=None):
        """Open a window.

        Args:
            window: Window instance to open
        """
        window.show()
        if window not in self.open_windows:
            self.open_windows.append(window)
        if id_ is not None:
            self.windows_by_id[id_] = window
        window.set_limits(self.gui.get_limits())

    def get_window_by_id(self, id_):
        """Returns the window registered with the given id.

        Args:
            id_: Window id to look for

        Returns:
            The window registered with the given id or None if not found
        """
        return self.windows_by_id.get(id_)

    def close_window(self, window):
        """Close a window.

        Args:
            window: Window instance to close
        """
        if window in self.open_windows:
            self.open_windows.remove(window)
        self.windows_by_id = {k: v for k, v in self.windows_by_id.items() if v is not window}
        window.hide()

    def close_all(self):
        """Close all open windows."""
        for window in list(self.open_windows):
            self.close_window(window)

    def close_last_open(self):
        """Close last opened window."""
        if self.open_windows:
            window = self.open_windows.pop()
            self.close_window(window)

    def window_closed(self, window):
        """Callback when a window is closed by user.

        Args:
            window: Window instance that was closed
        """
        if window in self.open_windows:
            self.open_windows.remove(window)
        self.windows_by_id = {k: v for k, v in self.windows_by_id.items() if v is not window}
