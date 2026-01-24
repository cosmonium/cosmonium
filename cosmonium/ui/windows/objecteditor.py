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
from ..editors.editors import ObjectEditors
from ..managers.window_manager import WindowManager
from .editor import ParamEditor


class ObjectEditorWindow(ParamEditor):

    def __init__(self, body, parent=None):
        ParamEditor.__init__(self, parent=parent)
        self.body = body
        self.editor = None

    def update_parameter(self, param):
        self.editor.update_user_parameters()

    def make_entries(self):
        self.editor = ObjectEditors.get_editor_for(self.body)
        return self.editor.get_user_parameters()


def _show_object_editor_window():
    """Show the object editor for selected object."""
    window_manager = WindowManager.instance()
    if not window_manager.get_window_by_id('object-editor') and window_manager.gui.cosmonium.selected is not None:
        # TODO: Retrieve properly selected object
        window = ObjectEditorWindow(window_manager.gui.cosmonium.selected, parent=window_manager.gui)
        window_manager.open_window(window, 'object-editor')


def register_object_editor_window():
    dispatcher = EventsDispatcher.instance()
    dispatcher.register('gui-show-editor', _show_object_editor_window)
