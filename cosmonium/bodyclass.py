#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
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


from panda3d.core import LColor


class BodyClass(object):
    def __init__(
        self, name=None, show=True, label_color=LColor(), orbit_color=LColor(), show_label=False, show_orbit=True
    ):
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
            print("Unknown body class '%s'" % body_class)
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
            return LColor(0.5, 0.5, 0.5, 1)

    def get_orbit_color(self, body_class):
        body_class = self.get_class(body_class)
        if body_class is not None:
            return body_class.orbit_color
        else:
            return LColor(0.5, 0.5, 0.5, 1)

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

bodyClasses.register_class(
    "galaxy",
    "galaxies",
    BodyClass(label_color=LColor(0.0, 0.45, 0.5, 1), orbit_color=LColor(1, 1, 1, 1), show_label=False),
)
bodyClasses.register_class(
    "globular",
    "globulars",
    BodyClass(label_color=LColor(0.8, 0.45, 0.5, 1), orbit_color=LColor(1, 1, 1, 1), show_label=False),
)
bodyClasses.register_class(
    "nebula",
    "nebulae",
    BodyClass(label_color=LColor(0.541, 0.764, 0.278, 1), orbit_color=LColor(1, 1, 1, 1), show_label=False),
)
bodyClasses.register_class(
    "star",
    "stars",
    BodyClass(label_color=LColor(0.471, 0.356, 0.682, 1), orbit_color=LColor(0.5, 0.5, 0.8, 1), show_label=False),
)
bodyClasses.register_class(
    "planet",
    "planets",
    BodyClass(label_color=LColor(0.407, 0.333, 0.964, 1), orbit_color=LColor(0.3, 0.323, 0.833, 1), show_label=False),
)
bodyClasses.register_class(
    "dwarfplanet",
    "dwarfplanets",
    BodyClass(label_color=LColor(0.407, 0.333, 0.964, 1), orbit_color=LColor(0.3, 0.323, 0.833, 1), show_label=False),
)
bodyClasses.register_class(
    "moon",
    "moons",
    BodyClass(label_color=LColor(0.231, 0.733, 0.792, 1), orbit_color=LColor(0.08, 0.407, 0.392, 1), show_label=False),
)
bodyClasses.register_class(
    "minormoon",
    "minormoons",
    BodyClass(label_color=LColor(0.231, 0.733, 0.792, 1), orbit_color=LColor(0.08, 0.407, 0.392, 1), show_label=False),
)
bodyClasses.register_class(
    "lostmoon",
    "lostmoons",
    BodyClass(
        label_color=LColor(0.231, 0.733, 0.792, 1),
        orbit_color=LColor(0.08, 0.407, 0.392, 1),
        show=False,
        show_label=False,
    ),
)
bodyClasses.register_class(
    "comet",
    "comets",
    BodyClass(label_color=LColor(0.768, 0.607, 0.227, 1), orbit_color=LColor(0.639, 0.487, 0.168, 1), show_label=False),
)
bodyClasses.register_class(
    "asteroid",
    "asteroids",
    BodyClass(label_color=LColor(0.596, 0.305, 0.164, 1), orbit_color=LColor(0.58, 0.152, 0.08, 1), show_label=False),
)
bodyClasses.register_class(
    "interstellar",
    "interstellars",
    BodyClass(label_color=LColor(0.596, 0.305, 0.164, 1), orbit_color=LColor(0.58, 0.152, 0.08, 1), show_label=False),
)
bodyClasses.register_class(
    "spacecraft",
    "spacecrafts",
    BodyClass(label_color=LColor(0.93, 0.93, 0.93, 1), orbit_color=LColor(0.4, 0.4, 0.4, 1), show_label=False),
)
bodyClasses.register_class(
    "constellation",
    "constellations",
    BodyClass(label_color=LColor(0.225, 0.301, 0.36, 1), orbit_color=LColor(0.0, 0.24, 0.36, 1.0), show_label=False),
)
bodyClasses.register_class("boundary", "boundaries", BodyClass(orbit_color=LColor(0.24, 0.10, 0.12, 1.0)))
