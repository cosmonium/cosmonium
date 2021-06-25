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


from panda3d.core import LVector3d, LVector3, LQuaternion, LColor, BitMask32, LQuaterniond, LPoint3d
from panda3d.core import DirectionalLight

from .foundation import BaseObject
from .stellarobject import StellarObject
from .anchors import StellarAnchor
from .systems import SimpleSystem
from .foundation import VisibleObject
from .shapes import SphereShape, ScaledSphereShape
from .surfaces import EllipsoidFlatSurface
from .appearances import Appearance
from .astro.frame import RelativeReferenceFrame, SynchroneReferenceFrame, J2000BarycentricEclipticReferenceFrame
from .astro.orbits import LocalFixedPosition
from .astro.rotations import FixedRotation, UnknownRotation
from .astro.astro import lum_to_abs_mag, abs_mag_to_lum, temp_to_radius
from .astro.spectraltype import SpectralType, spectralTypeStringDecoder
from .astro.blackbody import temp_to_RGB
from .astro import units
from .shaders import BasicShader, FlatLightingModel
from . import settings

from math import asin, pi

class ReferencePoint(StellarObject):
    virtual_object = True

class SurfaceFactory(object):
    def create(self, body):
        return None

class StellarBody(StellarObject):
    has_rotation_axis = True
    has_reference_axis = True

    def __init__(self, names, source_names, radius, oblateness=None, scale=None,
                 surface=None, surface_factory=None,
                 orbit=None, rotation=None,
                 atmosphere=None, ring=None, clouds=None,
                 body_class=None, point_color=None,
                 description=''):
        StellarObject.__init__(self, names, source_names, orbit, rotation, body_class, point_color, description)
        self.surface = None
        self.ring = ring
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
        if self.ring is not None:
            self.ring.set_body(self)
            self.ring.set_owner(self)
        self.anchor._extend = self.get_extend()

    def get_or_create_system(self):
        if self.system is None:
            print("Creating system for", self.get_name())
            system_orbit = self.anchor.orbit
            system_rotation = FixedRotation(LQuaterniond(), J2000BarycentricEclipticReferenceFrame())
            #TODO: The system name should be translated correctly
            self.system = SimpleSystem(self.get_name() + " System", source_names=[], primary=self, orbit=system_orbit, rotation=system_rotation)
            self.parent.add_child_fast(self.system)
            #system_orbit.set_body(self.system)
            orbit = LocalFixedPosition(frame=RelativeReferenceFrame(system_orbit.frame, self.system.anchor), frame_position=LPoint3d())
            self.set_orbit(orbit)
            if isinstance(self, Star):
                self.system.add_child_star_fast(self)
            else:
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
            self.surface = surface
            self.auto_surface = False

    def insert_surface(self, index, surface):
        self.surfaces.insert(index, surface)
        surface.set_body(self)
        surface.set_owner(self)

    def set_surface(self, surface):
        if not surface in self.surfaces: return
        if self.auto_surface: return
        if self.init_components:
            self.unconfigure_shape()
            self.remove_component(self.surface)
        self.surface = surface
        if self.init_components:
            self.add_component(self.surface)
            self.configure_shape()

    def find_surface(self, surface_name):
        surface_name = surface_name.lower()
        for surface in self.surfaces:
            if surface.get_name().lower() == surface_name:
                return surface
        for surface in self.surfaces:
            if surface.category is not None and surface.category.lower() == surface_name:
                return surface
        return None

    def create_components(self):
        StellarObject.create_components(self)
        if self.surface is None:
            self.create_surface()
            self.auto_surface = True
        self.components.add_component(self.surface)
        self.surface.set_oid_color(self.oid_color)
        if self.ring is not None:
            self.components.add_component(self.ring)
            self.ring.set_oid_color(self.oid_color)
        if self.clouds is not None:
            self.components.add_component(self.clouds)
            self.clouds.set_oid_color(self.oid_color)
        if self.atmosphere is not None:
            self.components.add_component(self.atmosphere)
            self.atmosphere.set_oid_color(self.oid_color)
        self.configure_shape()

    def remove_components(self):
        self.unconfigure_shape()
        StellarObject.remove_components(self)
        self.components.remove_component(self.surface)
        if self.auto_surface:
            self.surface = None
        self.components.remove_component(self.ring)
        self.components.remove_component(self.clouds)
        self.components.remove_component(self.atmosphere)

    def get_components(self):
        #TODO: This is a hack to be fixed in v0.3.0
        components = []
        if self.surface is not None:
            components.append(self.surface)
        if self.ring is not None:
            components.append(self.ring)
        if self.clouds is not None:
            components.append(self.clouds)
        if self.atmosphere is not None:
            components.append(self.atmosphere)
        return components

    def configure_shape(self):
        if self.surface is not None:
            self.surface.configure_shape()
        if self.ring is not None:
            self.ring.configure_shape()
        if self.clouds is not None:
            self.clouds.configure_shape()
        if self.atmosphere is not None:
            self.atmosphere.configure_shape()

    def unconfigure_shape(self):
        if self.atmosphere is not None:
            self.atmosphere.unconfigure_shape()
        if self.clouds is not None:
            self.clouds.unconfigure_shape()
        if self.ring is not None:
            self.ring.unconfigure_shape()
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

    def get_extend(self):
        if self.ring is not None:
            return self.ring.outer_radius
        elif self.surface is not None:
            return self.surface.get_max_radius()
        else:
            return self.get_apparent_radius()

    def get_height_under_xy(self, x, y):
        if self.surface is not None:
            return self.surface.get_height_at(x, y)
        else:
            #print("No surface")
            return self.radius

    def get_height_under(self, position):
        if self.surface is not None:
            (x, y, distance) = self.spherical_to_xy(self.cartesian_to_spherical(position))
            return self.surface.get_height_at(x, y)
        else:
            #print("No surface")
            return self.radius

    def get_normals_under_xy(self, x, y):
        if self.surface is not None:
            vectors = self.surface.get_normals_at(x, y)
        else:
            vectors = (LVector3d.up(), LVector3d.forward(), LVector3d.left())
        return vectors

    def get_normals_under(self, position):
        if self.surface is not None:
            (x, y, distance) = self.spherical_to_xy(self.cartesian_to_spherical(position))
            vectors = self.surface.get_normals_at(x, y)
        else:
            vectors = (LVector3d.up(), LVector3d.forward(), LVector3d.left())
        sync_frame = SynchroneReferenceFrame(self.anchor)
        return (sync_frame.get_orientation().xform(vectors[0]),
                sync_frame.get_orientation().xform(vectors[1]),
                sync_frame.get_orientation().xform(vectors[2]))

    def get_lonlatvert_under_xy(self, x, y):
        if self.surface is not None:
            vectors = self.surface.get_lonlatvert_at(x, y)
        else:
            vectors = (LVector3d.right(), LVector3d.forward(), LVector3d.up())
        return vectors

    def get_lonlatvert_under(self, position):
        if self.surface is not None:
            (x, y, distance) = self.spherical_to_xy(self.cartesian_to_spherical(position))
            vectors = self.surface.get_lonlatvert_at(x, y)
        else:
            vectors = (LVector3d.right(), LVector3d.forward(), LVector3d.up())
        sync_frame = SynchroneReferenceFrame(self.anchor)
        return (sync_frame.get_orientation().xform(vectors[0]),
                sync_frame.get_orientation().xform(vectors[1]),
                sync_frame.get_orientation().xform(vectors[2]))

    def show_clouds(self):
        if self.clouds:
            self.clouds.show()

    def hide_clouds(self):
        if self.clouds:
            self.clouds.hide()

    def toggle_clouds(self):
        if self.clouds:
            self.clouds.toggle_shown()

class ReflectiveBody(StellarBody):
    anchor_class = StellarAnchor.Reflective
    def __init__(self, *args, **kwargs):
        self.albedo = kwargs.pop('albedo', 0.5)
        StellarBody.__init__(self, *args, **kwargs)
        self.light_source = None
        #TODO: This should be done in create_anchor
        self.anchor._albedo = self.albedo

    def is_emissive(self):
        return False

    def get_phase(self):
        if self.anchor.vector_to_obs is None or self.anchor.vector_to_star is None: return 0.0
        angle = self.anchor.vector_to_obs.dot(self.anchor.vector_to_star)
        phase = (1.0 + angle) / 2.0
        return phase

    def start_shadows_update(self):
        for component in self.get_components():
            component.start_shadows_update()
        if self.ring is not None:
            if self.clouds is not None:
                self.ring.shadow_caster.add_target(self.clouds)
            if self.surface is not None:
                self.ring.add_shadow_target(self.surface)
                self.surface.add_shadow_target(self.ring)

    def add_shadow_target(self, target):
        for component in target.get_components():
            self.surface.add_shadow_target(component)

    def end_shadows_update(self):
        for component in self.get_components():
            component.end_shadows_update()

    def create_light(self):
        print("Create light for", self.get_name())
        self.directional_light = DirectionalLight('light_source')
        self.directional_light.setDirection(LVector3(*-self.anchor.vector_to_star))
        self.directional_light.setColor((1, 1, 1, 1))
        self.light_source = self.context.world.attachNewNode(self.directional_light)
        self.components.set_light(self.light_source)

    def update_light(self, camera_pos):
        pos = self.get_local_position() + self.anchor.vector_to_star * self.get_extend()
        BaseObject.place_pos_only(self.light_source, pos, camera_pos, self.anchor.distance_to_obs, self.anchor.vector_to_obs)
        self.directional_light.setDirection(LVector3(*-self.anchor.vector_to_star))

    def remove_light(self):
        self.light_source.remove_node()
        self.light_source = None
        self.directional_light = None

    def configure_shape(self):
        StellarBody.configure_shape(self)
        self.surface.create_shadows()

    def unconfigure_shape(self):
        StellarBody.unconfigure_shape(self)
        self.surface.remove_shadows()

    def create_components(self):
        StellarBody.create_components(self)
        if self.light_source is None:
            self.create_light()
            self.components.update_shader()

    def update_components(self, camera_pos):
        if self.light_source is not None:
            self.update_light(camera_pos)

    def remove_components(self):
        if self.light_source is not None:
            self.remove_light()
            self.components.update_shader()
        StellarBody.remove_components(self)

class EmissiveBody(StellarBody):
    anchor_class = StellarAnchor.Emissive
    has_halo = True
    has_resolved_halo = True
    def __init__(self, *args, **kwargs):
        abs_magnitude = kwargs.pop('abs_magnitude', None)
        StellarBody.__init__(self, *args, **kwargs)
        self.abs_magnitude = abs_magnitude
        #TODO: This should be done in create_anchor
        self.anchor._abs_magnitude = abs_magnitude

    def is_emissive(self):
        return True

    def get_luminosity(self):
        return abs_mag_to_lum(self.get_abs_magnitude())
    
    def get_phase(self):
        return 1

class StarTexSurfaceFactory(SurfaceFactory):
    def __init__(self, texture):
        self.texture = texture

    def create(self, body):
        shape = SphereShape()
        appearance = Appearance(emissionColor=body.point_color, texture=self.texture)
        shader = BasicShader(lighting_model=FlatLightingModel())
        return EllipsoidFlatSurface('surface',
                           radius=body.radius, oblateness=body.oblateness, scale=body.scale,
                           shape=shape, appearance=appearance, shader=shader)

class Star(EmissiveBody):
    def __init__(self, names, source_names, radius=None, oblateness=None, scale=None,
                 surface=None, surface_factory=None,
                 orbit=None, rotation=None,
                 abs_magnitude=None, temperature=None, spectral_type=None,
                 atmosphere=None, ring=None, clouds=None,
                 body_class='star',  point_color=None,
                 description=''):
        if spectral_type is None:
            self.spectral_type = SpectralType()
        elif isinstance(spectral_type, SpectralType):
            self.spectral_type = spectral_type
        else:
            self.spectral_type = spectralTypeStringDecoder.decode(spectral_type)
        if temperature is None:
            if spectral_type is None:
                self.temperature = units.sun_temperature
            else:
                self.temperature = self.spectral_type.temperature
        else:
            self.temperature = temperature
        if point_color is None:
            point_color = temp_to_RGB(self.temperature)
        if radius is None:
            if self.spectral_type.white_dwarf:
                #TODO: Find radius-luminosity relationship or use mass
                radius = 7000.0
            else:
                radius = temp_to_radius(self.temperature, abs_magnitude)
        EmissiveBody.__init__(self, names=names, source_names=source_names,
                              radius=radius, oblateness=oblateness, scale=scale,
                              surface=surface, surface_factory=surface_factory,
                              orbit=orbit, rotation=rotation,
                              abs_magnitude=abs_magnitude,
                              atmosphere=atmosphere, ring=ring, clouds=clouds,
                              body_class=body_class, point_color=point_color,
                              description=description)

class DeepSpaceObject(EmissiveBody):
    background = True
    has_rotation_axis = False
    has_reference_axis = False
    has_resolved_halo = False
    support_offset_body_center = False

    def __init__(self, names, source_names, radius, radius_units=units.Ly,
                 abs_magnitude=None,
                 surface=None,
                 orbit=None, rotation=None,
                 body_class=None, point_color=None,
                 description=''):
        radius = radius * radius_units
        EmissiveBody.__init__(self, names, source_names, radius=radius,
                              surface=surface,
                              orbit=orbit, rotation=rotation,
                              abs_magnitude=abs_magnitude,
                              body_class=body_class, point_color=point_color,
                              description=description)

    def get_height_under(self, position):
        return 0.0

    def check_and_update_instance(self, camera_pos, camera_rot):
        EmissiveBody.check_and_update_instance(self, camera_pos, camera_rot)
        app_magnitude = self.get_app_magnitude()
        self.surface.appearance.set_magnitude(self, self.surface.shape, self.surface.shader, self.abs_magnitude, app_magnitude, self.anchor.visible_size)

class SkySphere(VisibleObject):
    def __init__(self, names, shape=None, appearance=None, shader=None, orientation=None):
        #TODO: should be a ShapeObject instead !
        VisibleObject.__init__(self, names)
        self.appearance = appearance
        if orientation is None:
            orientation = UnknownRotation()
        self.orientation = orientation
        if shape is None:
            shape = ScaledSphereShape(self.context.observer.infinity, inv_texture_u=True)
        self.shape = shape
        self.shape.parent = self
        #TODO: should be done like that or should we have EmisionAppearance ?
        if appearance.emissionColor is None:
            appearance.emissionColor = LColor(1, 1, 1, 1)
        if shader is None:
            shader = BasicShader(lighting_model=FlatLightingModel())
        self.shader = shader

    def create_instance(self):
        if not self.instance:
            self.instance = self.shape.create_instance()
            if self.instance is None:
                return
        if self.appearance is not None:
            self.appearance.bake()
            self.appearance.apply(self)
        #Shader is applied once the textures are loaded
#         if self.shader is not None:
#             self.shader.apply(self.shape, self.appearance)
        self.instance.setQuat(LQuaternion(*self.orientation))
        self.instance.set_two_sided(True)
        self.instance.setCollideMask(BitMask32.allOff())
        self.instance.reparentTo(self.context.world)
        self.instance.setBin('background', settings.skysphere_depth)
        self.instance.set_depth_write(False)
