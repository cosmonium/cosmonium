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


from ...events import EventsDispatcher
from ... import version

from ..managers.window_manager import WindowManager
from .textwindow import TextWindow


about_text = (
    """# Cosmonium

**Version**: V%s
Copyright 2018-2026 Laurent Deru


**Website**: http://github.com/cosmonium/cosmonium


This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation; either version 3 of the License, or (at your option) any later
version.


This program uses several third-party libraries which are subject to their own
licenses, see Third-Party.md for the complete list.
"""
    % version.version_str
)


def _show_about_window():
    """Show the about window."""
    window_manager = WindowManager.instance()
    if not window_manager.get_window_by_id('about'):
        window = TextWindow('About', parent=window_manager.gui)
        window.set_text(about_text)
        window_manager.open_window(window, 'about')


def register_about_window():
    dispatcher = EventsDispatcher.instance()
    dispatcher.register('gui-show-about', _show_about_window)
