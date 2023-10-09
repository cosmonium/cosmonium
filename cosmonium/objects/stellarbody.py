#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2023 Laurent Deru.
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


from panda3d.core import LVector3d, LQuaterniond, LPoint3d

from .stellarobject import StellarObject
from .systems import SimpleSystem

from ..astro.frame import OrbitReferenceFrame, J2000BarycentricEclipticReferenceFrame
from ..astro.orbits import LocalFixedPosition
from ..astro.rotations import FixedRotation


class StellarBody(StellarObject):
    has_rotation_axis = True
    has_reference_axis = True

    def __init__(self, names, source_names, radius, oblateness=None, scale=None,
                 surface=None, surface_factory=None,
                 orbit=None, rotation=None, frame=None,
                 atmosphere=None, clouds=None,
                 body_class=None, point_color=None,
                 description=''):
        StellarObject.__init__(self, names, source_names, orbit, rotation, frame, body_class, point_color, description)
        self.surface = None
        self.clouds = clouds
        self.atmosphere = atmosphere
        self.surface = surface
        self.surface_factory = surface_factory
        self.surfaces = []
        self.auto_surface = surface is None
        if surface is not None:
            #TODO: Should not be done explicitly
            surface.set_body(self)
            surface.set_owner(self)
            self.surfaces.append(surface)
        self.radius = radius
        self.anchor._height_under = radius
        self.oblateness = oblateness
        self.scale = scale
        if self.clouds is not None:
            self.clouds.set_body(self)
            self.clouds.set_owner(self)
        if self.atmosphere is not None:
            self.atmosphere.set_body(self)
            self.atmosphere.set_owner(self)
        self.anchor.set_bounding_radius(self.get_bounding_radius())

    def get_or_create_system(self):
        if self.system is None:
            print("Creating system for", self.get_name())
            system_orbit = self.anchor.orbit
            system_rotation = FixedRotation(LQuaterniond(), J2000BarycentricEclipticReferenceFrame())
            #TODO: The system name should be translated correctly
            self.system = SimpleSystem(self.get_name() + " System", source_names=[], primary=self, orbit=system_orbit, rotation=system_rotation)
            if self.parent is not None:
                self.parent.add_child_fast(self.system)
            #system_orbit.set_body(self.system)
            orbit = LocalFixedPosition(frame=OrbitReferenceFrame(self.system.anchor), frame_position=LPoint3d())
            self.set_orbit(orbit)
            self.system.add_child_fast(self)
        return self.system

    def create_surface(self):
        self.surface = self.surface_factory.create(self)
        self.surface.set_body(self)
        self.surface.set_owner(self)

    def add_surface(self, surface):
        self.surfaces.append(surface)
        surface.set_body(self)
        surface.set_owner(self)
        if self.surface is None:
            self.auto_surface = False
            self.set_surface(surface)

    def insert_surface(self, index, surface):
        self.surfaces.insert(index, surface)
        surface.set_body(self)
        surface.set_owner(self)

    def set_surface(self, surface):
        if not surface in self.surfaces: return
        if self.auto_surface: return
        if self.init_components:
            self.unconfigure_shape()
            self.components.remove_component(self.surface)
            if self.atmosphere is not None:
                self.atmosphere.remove_shape_object(surface)
        self.surface = surface
        self.anchor.set_bounding_radius(self.get_bounding_radius())
        if self.init_components:
            self.surface.set_oid_color(self.oid_color)
            self.components.add_component(self.surface)
            if self.atmosphere is not None:
                self.atmosphere.add_shape_object(self.surface)
            self.configure_shape()

    def find_surface(self, surface_name):
        surface_name = surface_name.lower()
        for surface in self.surfaces:
            if surface.name is not None and surface.get_name().lower() == surface_name:
                return surface
        for surface in self.surfaces:
            if surface.category is not None and surface.category.lower() == surface_name:
                return surface
        return None

    def has_rings(self):
        # TODO: If this is the primary, we should seach in the children of the parent system if they are ring objects
        return False

    def create_components(self):
        StellarObject.create_components(self)
        if self.surface is None:
            self.create_surface()
            self.auto_surface = True
        self.components.add_component(self.surface)
        self.surface.set_oid_color(self.oid_color)
        if self.clouds is not None:
            self.components.add_component(self.clouds)
            self.clouds.set_oid_color(self.oid_color)
        if self.atmosphere is not None:
            self.components.add_component(self.atmosphere)
            self.atmosphere.set_oid_color(self.oid_color)
            self.atmosphere.add_shape_object(self.surface)
            if self.clouds is not None:
                self.atmosphere.add_shape_object(self.clouds)
        self.configure_shape()

    def remove_components(self):
        self.unconfigure_shape()
        StellarObject.remove_components(self)
        self.components.remove_component(self.surface)
        if self.auto_surface:
            self.surface = None
        self.components.remove_component(self.clouds)
        self.components.remove_component(self.atmosphere)

    def get_components(self):
        #TODO: This is a hack to be fixed in v0.3.0
        components = []
        if self.surface is not None:
            components.append(self.surface)
        if self.clouds is not None:
            components.append(self.clouds)
        if self.atmosphere is not None:
            components.append(self.atmosphere)
        return components

    def configure_shape(self):
        if self.surface is not None:
            self.surface.configure_shape()
        if self.clouds is not None:
            self.clouds.configure_shape()
        if self.atmosphere is not None:
            self.atmosphere.configure_shape()

    def unconfigure_shape(self):
        if self.atmosphere is not None:
            self.atmosphere.unconfigure_shape()
        if self.clouds is not None:
            self.clouds.unconfigure_shape()
        if self.surface is not None:
            self.surface.unconfigure_shape()

    def get_apparent_radius(self):
        return self.radius

    def get_min_radius(self):
        if self.surface is not None:
            return self.surface.get_min_radius()
        else:
            return self.get_apparent_radius()

    def get_average_radius(self):
        if self.surface is not None:
            return self.surface.get_average_radius()
        else:
            return self.get_apparent_radius()

    def get_max_radius(self):
        if self.surface is not None:
            return self.surface.get_max_radius()
        else:
            return self.get_apparent_radius()

    def get_bounding_radius(self):
        extend = 0
        if self.surface is not None and self.surface.is_spherical():
            extend = max(extend, self.surface.get_max_radius())
        else:
            extend = max(extend, self.get_apparent_radius())
        if self.atmosphere is not None:
            extend = max(extend, self.atmosphere.radius)
        return extend

    def local_to_surface_position(self, position):
        return self.anchor._orientation.conjugate().xform(position - self.anchor.get_local_position())

    def surface_to_local_position(self, position):
        return self.anchor.get_local_position() + self.anchor._orientation.xform(position)

    def get_point_under(self, position):
        surface_position = self.local_to_surface_position(position)
        if self.surface is not None:
            point = self.surface.get_point_under(surface_position)
        else:
            #print("No surface")
            point = surface_position.normalized() * self.radius
        return self.surface_to_local_position(point)

    def get_radius_under(self, position):
        if self.surface is not None:
            return self.surface.get_radius_under(self.local_to_surface_position(position))
        else:
            #print("No surface")
            return self.radius

    def get_height_under(self, position):
        if self.surface is not None:
            return self.surface.get_height_under(self.local_to_surface_position(position))
        else:
            #print("No surface")
            return self.radius

    def get_alt_under(self, position):
        if self.surface is not None:
            return self.surface.get_alt_under(self.local_to_surface_position(position))
        else:
            #print("No surface")
            return self.radius

    def get_tangent_plane_under(self, position):
        if self.surface is not None:
            vectors = self.surface.get_tangent_plane_under(self.local_to_surface_position(position))
        else:
            vectors = (LVector3d.right(), LVector3d.forward(), LVector3d.up())
        orientation = self.anchor._orientation
        return (orientation.xform(vectors[0]),
                orientation.xform(vectors[1]),
                orientation.xform(vectors[2]))

    def show_clouds(self):
        if self.clouds:
            self.clouds.show()

    def hide_clouds(self):
        if self.clouds:
            self.clouds.hide()

    def toggle_clouds(self):
        if self.clouds:
            self.clouds.toggle_shown()
