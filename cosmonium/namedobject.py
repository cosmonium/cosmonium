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

from .foundation import ObjectLabel

class NamedObject:
    def __init__(self, names, source_names, description=''):
        self.set_names(names)
        self.source_names = source_names
        self.description = description
        self.label = None

    def get_names(self):
        return self.names

    def set_names(self, names):
        if names is None:
            self.names = ['']
        elif isinstance(names, (list, tuple)):
            self.names = names
        else:
            self.names = [names]

    def get_friendly_name(self):
        return self.names[0]

    def get_name(self):
        return self.names[0]

    def get_c_name(self):
        return self.source_names[0] if self.source_names else self.names[0]

    def get_ascii_name(self):
        return self.get_c_name().encode('ascii', 'replace').decode('ascii').replace('?', 'x').lower()

    def get_exact_name(self, text):
        text = text.upper()
        result = ''
        for name in self.names:
            if name.upper() == text:
                result = name
                break
        else:
            for name in self.source_names:
                if name.upper() == text:
                    result = name
                    break
        return result

    def get_fullname(self, separator='/'):
        return self.get_c_name()

    def get_description(self):
        return self.description

    def create_label_instance(self):
        return ObjectLabel(self.get_ascii_name() + '-label', self)

    def create_label(self):
        if self.label is None:
            self.label = self.create_label_instance()

    def remove_label(self):
        if self.label is not None:
            self.label.remove_instance()
            self.label = None

    def show_label(self):
        if self.label:
            self.label.show()

    def hide_label(self):
        if self.label:
            self.label.hide()

    def toggle_label(self):
        if self.label:
            self.label.toggle_shown()
