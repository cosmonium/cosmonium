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
from ..managers.window_manager import WindowManager
from .objecteditor import ObjectEditorWindow


def _show_ship_editor_window():
    """Show the object editor for the ship."""
    window_manager = WindowManager.instance()
    if not window_manager.get_window_by_id('ship-editor') and window_manager.gui.cosmonium.ship is not None:
        # TODO: Retrieve properly ship object
        window = ObjectEditorWindow(window_manager.gui.cosmonium.ship, parent=window_manager.gui)
        window_manager.open_window(window, 'ship-editor')


def register_ship_editor_window():
    dispatcher = EventsDispatcher.instance()
    dispatcher.register('gui-show-ship-editor', _show_ship_editor_window)
