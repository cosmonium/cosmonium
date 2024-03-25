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


from ..editors.editors import ObjectEditors
from .editor import ParamEditor


class ObjectEditorWindow(ParamEditor):
    def __init__(self, font_family, font_size=14, owner=None):
        ParamEditor.__init__(self, font_family, font_size=font_size, owner=owner)
        self.editor = None

    def update_parameter(self, param):
        self.editor.update_user_parameters()

    def make_entries(self, body):
        self.editor = ObjectEditors.get_editor_for(body)
        return self.editor.get_user_parameters()
