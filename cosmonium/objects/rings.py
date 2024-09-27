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


from ..engine.anchors import StellarAnchor

from .stellarobject import StellarObject


class StellarRings(StellarObject):
    anchor_class = StellarAnchor.Reflective
    spread_object = True

    def __init__(
        self, names, source_names, rings_object, orbit, rotation, frame, body_class, point_color, description=''
    ):
        StellarObject.__init__(self, names, source_names, orbit, rotation, frame, body_class, point_color, description)
        self.rings_object = rings_object
        self.rings_object.set_body(self)
        self.rings_object.set_owner(self)
        self.surface = rings_object
        self.anchor._height_under = self.rings_object.outer_radius
        self.anchor.set_bounding_radius(self.get_bounding_radius())

    def is_emissive(self):
        return False

    def get_phase(self):
        return 1.0

    def get_apparent_radius(self):
        return self.rings_object.outer_radius

    def start_shadows_update(self):
        for component in self.get_components():
            component.start_shadows_update()

    def self_shadows_update(self, light_source):
        pass

    def add_shadow_target(self, light_source, target):
        for component in target.get_components():
            self.rings_object.add_shadow_target(light_source, component)

    def end_shadows_update(self):
        for component in self.get_components():
            component.end_shadows_update()

    def create_components(self):
        StellarObject.create_components(self)
        self.components.add_component(self.rings_object)
        self.rings_object.set_oid_color(self.oid_color)
        self.configure_shape()

    def remove_components(self):
        self.unconfigure_shape()
        StellarObject.remove_components(self)

    def get_components(self):
        components = []
        components.append(self.rings_object)
        return components

    def configure_shape(self):
        self.rings_object.configure_shape()

    def unconfigure_shape(self):
        self.rings_object.unconfigure_shape()
