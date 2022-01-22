#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2022 Laurent Deru.
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



from ...foundation import LabelledObject
from ...namedobject import NamedObject
from ...bodyclass import bodyClasses
from ... import settings

from .background_label import BackgroundLabel


class Constellation(NamedObject, LabelledObject):
    ignore_light = True
    default_shown = True
    background_level = settings.constellations_depth
    body_class = 'constellation'

    def __init__(self, name, center, boundary):
        NamedObject.__init__(self, name, [])
        LabelledObject.__init__(self, name)
        self.center = center
        self.boundary = boundary
        self.create_components()

    def create_label_instance(self):
        return BackgroundLabel(self.get_ascii_name() + '-label', self)

    def create_components(self):
        self.create_label()
        self.add_component(self.label)
        self.add_component(self.boundary)

    def project(self, time, center, distance):
        return self.center.project(time, center, distance)

    def get_label_text(self):
        return self.get_name()

    def get_label_color(self):
        return bodyClasses.get_label_color(self.body_class)

    def get_label_size(self):
        return settings.constellations_label_size
