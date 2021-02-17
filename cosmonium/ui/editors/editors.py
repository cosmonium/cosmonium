#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2021 Laurent Deru.
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

from ...parameters import ParametersList

class ObjectEditors:
    editors = []
    editors_map = {}

    @classmethod
    def register(cls, object_class, editor):
        cls.editors_map[object_class] = editor
        cls.editors.insert(0, (object_class, editor))

    @classmethod
    def get_editor_for(cls, object_to_edit):
        editor = cls.editors_map.get(object_to_edit.__class__, None)
        if editor is None:
            for entry in cls.editors:
                (object_class, object_editor) = entry
                if isinstance(object_to_edit, object_class):
                    editor = object_editor
                    break
        if editor is None:
            print(_("Unknown object type"), object_to_edit.__class__.__name__)
            editor = EmptyEditor
        return editor(object_to_edit)

class EditorWrapper:
    def __init__(self, wrapped_object):
        self.wrapped_object = wrapped_object

    def get_user_parameters(self):
        return self.wrapped_object.get_user_parameters()

    def update_user_parameters(self):
        return self.wrapped_object.update_user_parameters()

class EmptyEditor:
    def __init__(self, object_to_edit):
        pass

    def get_user_parameters(self):
        return ParametersList()

    def update_user_parameters(self):
        pass
