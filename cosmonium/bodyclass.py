from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import LColor

class BodyClass(object):
    def __init__(self, label_color=LColor(), orbit_color=LColor(), show_label=False, show_orbit=True):
        self.label_color = label_color
        self.orbit_color = orbit_color
        self.show_label = show_label
        self.show_orbit = show_orbit
        self.show = True
        self.name = None

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

    def show(self, body_class):
        body_class = self.get_class(body_class)
        if body_class is not None:
            body_class.show = True

    def hide(self, body_class):
        body_class = self.get_class(body_class)
        if body_class is not None:
            body_class.show = False

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

    def show_label(self, body_class):
        body_class = self.get_class(body_class)
        if body_class is not None:
            body_class.show_label = True

    def hide_label(self, body_class):
        body_class = self.get_class(body_class)
        if body_class is not None:
            body_class.show_label = False

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

    def show_orbit(self, body_class):
        body_class = self.plural_mapping.get(body_class, body_class)
        if body_class in self.classes:
            body_class.show_orbit = True

    def hide_orbit(self, body_class):
        body_class = self.get_class(body_class)
        if body_class is not None:
            body_class.show_orbit = False

    def toggle_show_orbit(self, body_class):
        body_class = self.get_class(body_class)
        if body_class is not None:
            body_class.show_orbit = not body_class.show_orbit
            print("Orbit '%s' : " % body_class.name, 'visible' if body_class.show_orbit else 'hidden')

bodyClasses = BodyClasses()
