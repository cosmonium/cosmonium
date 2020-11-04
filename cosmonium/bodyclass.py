#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2019 Laurent Deru.
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

from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import LColor

class BodyClass(object):
    def __init__(self, name=None, show=True, label_color=LColor(), orbit_color=LColor(), show_label=False, show_orbit=True):
        self.label_color = label_color
        self.orbit_color = orbit_color
        self.show_label = show_label
        self.show_orbit = show_orbit
        self.show = show
        self.name = name

class BodyClasses(object):
    def __init__(self):
        self.classes = {}
        self.plural_mapping = {}

    def register_class(self, name, plural, body_class):
        body_class.name = name
        self.classes[name] = body_class
        self.plural_mapping[plural] = name

    def get_class(self, body_class):
        body_class = self.plural_mapping.get(body_class, body_class)
        if body_class in self.classes:
            return self.classes[body_class]
        else:
            print("Unknown body class '%s", body_class)
            return None

    def get_show(self, body_class):
        body_class = self.get_class(body_class)
        if body_class is not None:
            return body_class.show
        else:
            return False

    def set_show(self, body_class, value):
        body_class = self.get_class(body_class)
        if body_class is not None:
            body_class.show = value
            print("Body '%s' : " % body_class.name, 'visible' if body_class.show else 'hidden')

    def show(self, body_class):
        self.set_show(body_class, True)

    def hide(self, body_class):
        self.set_show(body_class, False)

    def toggle_show(self, body_class):
        body_class = self.get_class(body_class)
        if body_class is not None:
            body_class.show = not body_class.show
            print("Body '%s' : " % body_class.name, 'visible' if body_class.show else 'hidden')

    def get_label_color(self, body_class):
        body_class = self.get_class(body_class)
        if body_class is not None:
            return body_class.label_color
        else:
            return LColor(.5, .5, .5, 1)

    def get_orbit_color(self, body_class):
        body_class = self.get_class(body_class)
        if body_class is not None:
            return body_class.orbit_color
        else:
            return LColor(.5, .5, .5, 1)

    def get_show_label(self, body_class):
        body_class = self.get_class(body_class)
        if body_class is not None:
            return body_class.show_label
        return False

    def set_show_label(self, body_class, value):
        body_class = self.get_class(body_class)
        if body_class is not None:
            body_class.show_label = value
            print("Label '%s' : " % body_class.name, 'visible' if body_class.show_label else 'hidden')

    def show_label(self, body_class):
        self.set_show_label(body_class, True)

    def hide_label(self, body_class):
        self.set_show_label(body_class, False)

    def toggle_show_label(self, body_class):
        body_class = self.get_class(body_class)
        if body_class is not None:
            body_class.show_label = not body_class.show_label
            print("Label '%s' : " % body_class.name, 'visible' if body_class.show_label else 'hidden')

    def get_show_orbit(self, body_class):
        body_class = self.get_class(body_class)
        if body_class is not None:
            return body_class.show_orbit
        return False

    def set_show_orbit(self, body_class, value):
        body_class = self.get_class(body_class)
        if body_class is not None:
            body_class.show_orbit = value
            print("Orbit '%s' : " % body_class.name, 'visible' if body_class.show_orbit else 'hidden')

    def show_orbit(self, body_class):
        self.set_show_orbit(body_class, True)

    def hide_orbit(self, body_class):
        self.set_show_orbit(body_class, False)

    def toggle_show_orbit(self, body_class):
        body_class = self.get_class(body_class)
        if body_class is not None:
            body_class.show_orbit = not body_class.show_orbit
            print("Orbit '%s' : " % body_class.name, 'visible' if body_class.show_orbit else 'hidden')

bodyClasses = BodyClasses()
