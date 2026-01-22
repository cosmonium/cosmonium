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
from ... import settings
from ..managers.window_manager import WindowManager
from .filewindow import FileWindow


def _show_open_script_window():
    """Show file selection dialog for opening a script."""
    window_manager = WindowManager.instance()
    if not window_manager.get_window_by_id('open-script'):
        window = FileWindow(
            'Select',
            settings.last_script_path,
            window_manager.gui.load_cel_script,
            extensions=['.cel', '.CEL'],
            owner=window_manager.gui,
        )
        window_manager.open_window(window, 'open-script')


def register_open_script_window():
    dispatcher = EventsDispatcher.instance()
    dispatcher.register('open-script', _show_open_script_window)
