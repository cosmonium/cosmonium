from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import LPoint3d, LVector3d, LVector3, LQuaternion, LQuaterniond, LColor, BitMask32
from panda3d.core import DirectionalLight

from .foundation import VisibleObject, CompositeObject, ObjectLabel, LabelledObject
from .shapes import SphereShape, ScaledSphereShape
from .surfaces import FlatSurface
from .appearances import Appearance
from .annotations import ReferenceAxis, RotationAxis, Orbit
from .astro.frame import SynchroneReferenceFrame
from .astro.orbits import FixedOrbit, FixedPosition
from .astro.rotations import FixedRotation
from .astro.astro import abs_to_app_mag, lum_to_abs_mag, abs_mag_to_lum, temp_to_radius
from .astro.spectraltype import SpectralType, spectralTypeStringDecoder
from .astro.blackbody import temp_to_RGB
from .astro import units
from .shaders import BasicShader, FlatLightingModel
from .bodyclass import bodyClasses
from .catalogs import objectsDB
from . import settings
from .settings import smallest_glare_mag
from .utils import mag_to_scale
from math import pi, asin, atan2, sin, cos

class StellarBodyLabel(ObjectLabel):
    def check_visibility(self, pixel_size):
        if hasattr(self.parent, "primary") and self.parent.resolved:
            self.visible = False
            return
        if self.parent.system is not None:
            body = self.parent.system
        else:
            body = self.parent
        if self.parent.visible and self.parent.resolved:
            self.visible = True
            self.fade = 1.0
        else:
            if body.distance_to_obs > 0.0:
                size = body.orbit.get_apparent_radius() / (body.distance_to_obs * pixel_size)
                self.visible = size > settings.label_fade
                self.fade = min(1.0, max(0.0, (size - settings.orbit_fade) / settings.orbit_fade))
        self.fade = clamp(self.fade, 0.0, 1.0)

    def update_instance(self, camera_pos, orientation):
        if self.parent.is_emissive() and (not self.parent.resolved or isinstance(self.parent, DeepSpaceObject)):
            if self.parent.scene_position != None:
                self.instance.setPos(*self.parent.scene_position)
                scale = abs(self.context.observer.pixel_size * self.parent.get_label_size() * self.parent.scene_distance)
            else:
                scale = 0.0
        else:
            offset = self.parent.get_apparent_radius() * 1.01
            front_pos = self.parent._local_position - orientation.xform(LPoint3d(0, offset, 0))
            vector_to_obs = LVector3d(camera_pos - front_pos)
            distance_to_obs = vector_to_obs.length()
            vector_to_obs /= distance_to_obs
            position, distance, scale_factor = self.get_real_pos(front_pos, camera_pos, distance_to_obs, vector_to_obs)
            self.instance.setPos(*position)
            scale = abs(self.context.observer.pixel_size * self.parent.get_label_size() * distance)
        color = self.parent.get_label_color() * self.fade
        self.look_at.set_pos(LVector3(*(orientation.xform(LVector3d.forward()))))
        self.label_instance.look_at(self.look_at, LVector3(), LVector3(*(orientation.xform(LVector3d.up()))))
        color[3] = 1.0
        self.label.setTextColor(color)
        if scale < 1e-7:
            print("Label too far", self.get_name())
            scale = 1e-7
        self.instance.setScale(scale)

class FixedOrbitLabel(StellarBodyLabel):
    def check_visibility(self, pixel_size):
        self.visible = self.parent._app_magnitude < settings.label_lowest_app_magnitude
        self.fade = 0.2 + (settings.label_lowest_app_magnitude - self.parent._app_magnitude) / (settings.label_lowest_app_magnitude - settings.max_app_magnitude)
        self.fade = clamp(self.fade, 0.0, 1.0)

class StellarObject(LabelledObject):
    has_rotation_axis = False
    has_reference_axis = False
    has_orbit = True
    has_halo = False
    has_resolved_halo = False
    virtual_object = False
    support_offset_body_center = True

    def __init__(self, names, orbit=None, rotation=None, body_class=None, point_color=None, description=''):
        LabelledObject.__init__(self, names)
        self.description = description
        self.system = None
        self.body_class = body_class
        if orbit is None:
            orbit = FixedOrbit()
        self.orbit = orbit
        if rotation is None:
            rotation = FixedRotation()
        self.rotation = rotation
        if point_color is None:
            point_color = LColor(1.0, 1.0, 1.0, 1.0)
        self.point_color = point_color
        self.abs_magnitude = 99.0
        #Flags
        self.visible = True #TODO: Should be False at init
        self.resolved = True #TODO: Should be False at init
        self.in_view = False
        self.selected = False
        #Cached values
        self._position = LPoint3d()
        self._global_position = LPoint3d()
        self._local_position = LPoint3d()
        self._orbit_position = LPoint3d()
        self._orbit_rotation = LQuaterniond()
        self._orientation = LQuaterniond()
        self._equatorial = LQuaterniond()
        self._app_magnitude = None
        self._extend = 0.0
        #Scene parameters
        self.rel_position = None
        self.distance_to_obs = None
        self.vector_to_obs = None
        self.distance_to_star = None
        self.vector_to_star = None
        self.height_under = 0.0
        self.star = None
        self.light_color = (1.0, 1.0, 1.0, 1.0)
        self.visible_size = 0.0
        self.scene_position = None
        self.scene_orientation = None
        self.scene_scale_factor = None
        self.world_body_center_offset = LVector3d()
        self.model_body_center_offset = LVector3d()
        self.projected_world_body_center_offset = LVector3d()
        #Components
        self.orbit_object = None
        self.rotation_axis = None
        self.reference_axis = None
        self.init_annotations = False
        self.init_components = False
        self.update_frozen = False
        #TODO: Should be done properly
        self.orbit.body = self
        self.rotation.body = self
        objectsDB.add(self)

    def check_settings(self):
        LabelledObject.check_settings(self)
        if self.body_class is None:
            print("No class for", self.get_name())
            return
        self.set_shown(bodyClasses.get_show(self.body_class))

    def get_fullname(self, separator='/'):
        if hasattr(self.parent, "primary") and self.parent.primary is not None:
            fullname = self.parent.parent.get_fullname(separator)
        else:
            fullname = self.parent.get_fullname(separator)
        if fullname != '':
            return fullname + separator + self.get_friendly_name()
        else:
            return self.get_friendly_name()

    def create_label_instance(self):
        if isinstance(self.orbit, FixedPosition):
            return FixedOrbitLabel(self.get_ascii_name() + '-label')
        else:
            return StellarBodyLabel(self.get_ascii_name() + '-label')

    def get_description(self):
        return self.description

    def create_annotations(self):
        if self.has_orbit and self.orbit.dynamic:
            self.create_orbit_object()
        self.init_annotations = True

    def create_components(self):
        if self.has_rotation_axis:
            self.rotation_axis = RotationAxis(self)
            self.add_component(self.rotation_axis)
        if self.has_reference_axis:
            self.reference_axis = ReferenceAxis(self)
            self.add_component(self.reference_axis)
        self.init_components = True

    def update_components(self, camera_pos):
        pass

    def remove_components(self):
        self.remove_component(self.rotation_axis)
        self.rotation_axis = None
        self.remove_component(self.reference_axis)
        self.reference_axis = None
        self.init_components = False

    def remove_annotations(self):
        self.remove_component(self.orbit_object)
        self.orbit_object = None
        self.init_annotations = False

    def set_system(self, system):
        self.system = system

    def set_body_class(self, body_class):
        self.body_class = body_class

    def create_orbit_object(self):
        if self.orbit_object is None and not isinstance(self.orbit, FixedOrbit) and not isinstance(self.orbit, FixedPosition):
            self.orbit_object = Orbit(self)
            self.add_component(self.orbit_object)

    def set_orbit(self, orbit):
        if self.orbit_object is not None:
            self.remove_component(self.orbit_object)
            self.orbit_object = None
        self.orbit = orbit
        self.orbit.body = self
        if self.has_orbit and self.init_annotations:
            self.create_orbit_object()

    def set_rotation(self, rotation):
        self.rotation = rotation
        if self.rotation:
            self.rotation.body = self

    def find_by_name(self, name, name_up=None):
        if self.is_named(name, name_up):
            return self
        else:
            return None

    def is_named(self, name, name_up=None):
        if name_up is None:
            name_up = name.upper()
        for name in self.names:
            if name.upper() == name_up:
                return True
        else:
            return False

    def set_selected(self, selected):
        self.selected = selected
        if self.orbit_object:
            self.orbit_object.set_selected(selected)
        else:
            if self.parent:
                self.parent.set_selected(selected)

    def set_parent(self, parent):
        CompositeObject.set_parent(self, parent)
        self.orbit.frame.set_parent_body(self.parent)
        self.rotation.frame.set_parent_body(self.parent)
        self.create_orbit_object()

    def set_star(self, star):
        self.star = star

    def is_emissive(self):
        return False

    def get_label_color(self):
        return bodyClasses.get_label_color(self.body_class)

    def get_label_size(self):
        return settings.label_size

    def get_label_text(self):
        return self.get_name()

    def get_orbit_color(self):
        return bodyClasses.get_orbit_color(self.body_class)

    def get_apparent_radius(self):
        return 0

    def get_extend(self):
        return self.get_apparent_radius()

    def calc_height_under(self, camera_pos):
        self.height_under = self.get_height_under(camera_pos)

    def get_abs_magnitude(self):
        return 99.0

    def get_app_magnitude(self):
        if self.distance_to_obs != None and self.distance_to_obs > 0:
            return abs_to_app_mag(self.get_abs_magnitude(), self.distance_to_obs)
        return 99.0

    def get_global_position(self):
        #TODO: should be done in frame
        #TODO: cache value for given time
        global_position = self.parent.get_global_position() + self.orbit.get_global_position_at(0)
        return global_position

    def get_local_position(self):
        return self.orbit.frame.get_local_position(self._orbit_rotation.xform(self._orbit_position))

    def get_position(self):
        return self.get_global_position() + self.get_local_position()

    def get_rel_position_to(self, position):
        return (self.get_global_position() - position) + self.get_local_position()

    def get_abs_rotation(self):
        return self.rotation.frame.get_abs_orientation(self._orientation)

    def get_equatorial_rotation(self):
        return self.rotation.frame.get_abs_orientation(self._equatorial)

    def get_sync_rotation(self):
        return self.rotation.frame.get_abs_orientation(self._orientation)

    def cartesian_to_spherical(self, position):
        sync_frame = SynchroneReferenceFrame(self)
        rel_position = sync_frame.get_rel_position(position)
        distance = rel_position.length()
        if distance > 0:
            theta = asin(rel_position[2] / distance)
            if rel_position[0] != 0.0:
                phi = atan2(rel_position[1], rel_position[0])
                #Offset phi by 180 deg with proper wrap around
                #phi = (phi + pi + pi) % (2 * pi) - pi
            else:
                phi = 0.0
        else:
            phi = 0.0
            theta = 0.0
        return (phi, theta, distance)

    def spherical_to_cartesian(self, position):
        (phi, theta, distance) = position
        #Offset phi by 180 deg with proper wrap around
        #phi = (phi + pi + pi) % (2 * pi) - pi
        rel_position = LPoint3d(cos(theta) * cos(phi), cos(theta) * sin(phi), sin(theta))
        rel_position *= distance
        sync_frame = SynchroneReferenceFrame(self)
        position = sync_frame.get_local_position(rel_position)
        return position

    def spherical_to_longlat(self, position):
        (phi, theta, distance) = position
        x = phi / pi / 2 + 0.5
        y = 1.0 - (theta / pi + 0.5)
        return (x, y, distance)

    def longlat_to_spherical(self, position):
        (x, y, distance) = position
        phi = (x - 0.5) * pi / 2
        tetha = (1.0 - y - 0.5) * pi
        return (phi, tetha, distance)

    def calc_global_distance_to(self, position):
        direction = self.get_position() - position
        length = direction.length()
        return (direction / length, length)

    def calc_local_distance_to(self, position):
        direction = position - self.get_local_position()
        length = direction.length()
        return (direction / length, length)

    def get_height_under(self, position):
        return self.get_apparent_radius()

    def calc_visible_size(self, pixel_size):
        if self.distance_to_obs > 0.0:
            return self.get_extend() / (self.distance_to_obs * pixel_size)
        else:
            return 0.0

    def update(self, time):
        self._orbit_position = self.orbit.get_position_at(time)
        self._orbit_rotation = self.orbit.get_rotation_at(time)
        self._orientation = self.rotation.get_rotation_at(time)
        self._equatorial = self.rotation.get_equatorial_rotation_at(time)
        self._local_position = self.orbit.frame.get_local_position(self._orbit_rotation.xform(self._orbit_position))
        self._global_position = self.parent._global_position + self.orbit.get_global_position_at(time)
        self._position = self._global_position + self._local_position
        if self.star:
            (self.vector_to_star, self.distance_to_star) = self.calc_local_distance_to(self.star.get_local_position())
        CompositeObject.update(self, time)
        self.update_frozen = not self.resolved and not (self.orbit.dynamic or self.rotation.dynamic)

    def update_obs(self, observer):
        global_delta = self._global_position - observer.camera_global_pos
        local_delta = self._local_position - observer._position
        self.rel_position = global_delta + local_delta
        length = self.rel_position.length()
        self.vector_to_obs = -self.rel_position / length
        self.distance_to_obs = length
        self.cos_view_angle = observer.camera_vector.dot(-self.vector_to_obs)
        CompositeObject.update_obs(self, observer)

    def check_visibility(self, pixel_size):
        if self.distance_to_obs > 0.0:
            self.visible_size = self._extend / (self.distance_to_obs * pixel_size)
        else:
            self.visible_size = 0.0
        self._app_magnitude = self.get_app_magnitude()
        self.resolved = self.visible_size > settings.min_body_size
        if self.resolved:
            radius = self.get_extend()
            if self.distance_to_obs > radius:
                D = self.rel_position + (self.context.observer.camera_vector * (radius * self.context.observer.inv_sin_dfov))
                len_squared = D.dot(D)
                e = D.dot(self.context.observer.camera_vector)
                self.in_view = e >= 0.0 and e*e > len_squared * self.context.observer.sqr_cos_dfov
                #TODO: add check if object is slightly behind the observer
            else:
                #We are in the object
                self.in_view = True
        else:
            #Don't bother checking the visibility of a point
            self.in_view = True
        self.visible = self.in_view and (self.visible_size > 1.0 or self._app_magnitude < settings.lowest_app_magnitude)
        if not self.virtual_object and self.resolved and self.in_view:
            self.context.add_visible(self)
        LabelledObject.check_visibility(self, pixel_size)

    def check_and_update_instance(self, camera_pos, orientation, pointset):
        if self.support_offset_body_center and self.visible and self.resolved and settings.offset_body_center:
            height = self.get_height_under(camera_pos)
            self.scene_rel_position = self.rel_position + self.vector_to_obs * height
            distance_to_obs = self.distance_to_obs - height
        else:
            self.scene_rel_position = self.rel_position
            distance_to_obs = self.distance_to_obs
        self.scene_position, self.scene_distance, self.scene_scale_factor = self.get_real_pos_rel(self.scene_rel_position, distance_to_obs, self.vector_to_obs)
        self.scene_orientation = self.get_abs_rotation()
        if self.label is None:
            self.create_label()
        if self.visible:
            if not self.init_annotations:
                self.create_annotations()
                self.check_settings()
            if self.resolved:
                if self.support_offset_body_center and settings.offset_body_center:
                    self.world_body_center_offset = -self.vector_to_obs * self.height_under * self.scene_scale_factor
                    self.model_body_center_offset = self.scene_orientation.conjugate().xform(-self.vector_to_obs) * self.height_under / self.get_apparent_radius()
                if not self.init_components:
                    self.create_components()
                    self.check_settings()
                self.update_components(camera_pos)
                if self.visible_size < settings.min_body_size * 2:
                    self.update_point(pointset)
                if self.has_resolved_halo and self._app_magnitude < smallest_glare_mag:
                    self.update_halo()
            else:
                if self.init_components:
                    self.remove_components()
                self.update_point(pointset)
        else:
            if not self.resolved:
                if self.init_components:
                    self.remove_components()
        CompositeObject.check_and_update_instance(self, camera_pos, orientation, pointset)

    def remove_instance(self):
        CompositeObject.remove_instance(self)
        if self.init_components:
            self.remove_components()
        if self.init_annotations:
            self.remove_annotations()
        self.remove_label()

    def update_point(self, pointset):
        scale = mag_to_scale(self._app_magnitude)
        if scale > 0:
            color = self.point_color * scale
            size = max(pointset.min_size, pointset.min_size + scale * settings.mag_pixel_scale)
            pointset.add_point(self.scene_position, color, size)
            if self.has_halo and self._app_magnitude < smallest_glare_mag:
                self.update_halo()

    def update_halo(self):
        if not settings.show_halo: return
        coef = smallest_glare_mag - self._app_magnitude + 6.0
        radius = self.visible_size
        if radius < 1.0:
            radius = 1.0
        size = radius * coef * 2.0
        position = self.scene_position
        self.context.haloset.add_point(LVector3(*position), self.point_color, size * 2)

    def show_rotation_axis(self):
        if self.rotation_axis:
            self.rotation_axis.show()

    def hide_rotation_axis(self):
        if self.rotation_axis:
            self.rotation_axis.hide()

    def toggle_rotation_axis(self):
        if self.rotation_axis:
            self.rotation_axis.toggle_shown()

    def show_reference_axis(self):
        if self.reference_axis:
            self.reference_axis.show()

    def hide_reference_axis(self):
        if self.reference_axis:
            self.reference_axis.hide()

    def toggle_reference_axis(self):
        if self.reference_axis:
            self.reference_axis.toggle_shown()

    def show_orbit(self):
        if self.orbit_object:
            self.orbit_object.show()

    def hide_orbit(self):
        if self.orbit_object:
            self.orbit_object.hide()

    def toggle_orbit(self):
        if self.orbit_object:
            self.orbit_object.toggle_shown()

class ReferencePoint(StellarObject):
    pass

class SurfaceFactory(object):
    def create(self, body):
        return None

class StellarBody(StellarObject):
    has_rotation_axis = True
    has_reference_axis = True

    def __init__(self, names, radius, oblateness=None, scale=None,
                 surface=None, surface_factory=None,
                 orbit=None, rotation=None,
                 atmosphere=None, ring=None, clouds=None,
                 body_class=None, point_color=None,
                 description=''):
        StellarObject.__init__(self, names, orbit, rotation, body_class, point_color, description)
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
            surface.owner = self
            self.surfaces.append(surface)
        self.radius = radius
        self.height_under = radius
        self.oblateness = oblateness
        self.scale = scale
        if self.clouds is not None:
            self.clouds.owner = self
        if self.atmosphere is not None:
            self.atmosphere.owner = self
        self._extend = self.get_extend()

    def create_surface(self):
        self.surface = self.surface_factory.create(self)

    def add_surface(self, surface):
        self.surfaces.append(surface)
        surface.owner = self

    def set_surface(self, surface):
        if not surface in self.surfaces: return
        if self.auto_surface: return
        if self.init_components:
            self.remove_component(self.surface)
        self.surface = surface
        if self.init_components:
            self.add_component(self.surface)
            self.configure_shape()

    def create_components(self):
        StellarObject.create_components(self)
        if self.surface is None:
            self.create_surface()
            #TODO: Should not be done explicitly
            self.surface.owner = self
            self.auto_surface = True
        self.add_component(self.surface)
        self.add_component(self.ring)
        self.add_component(self.clouds)
        self.add_component(self.atmosphere)        
        self.configure_shape()

    def remove_components(self):
        StellarObject.remove_components(self)
        self.remove_component(self.surface)
        if self.auto_surface:
            self.surface = None
        self.remove_component(self.ring)
        self.remove_component(self.clouds)
        self.remove_component(self.atmosphere)

    def configure_shape(self):
        if self.scale is not None:
            scale = self.scale
        elif self.oblateness is not None:
            scale = LVector3(1.0, 1.0, 1.0 - self.oblateness) * self.radius
        else:
            scale = LVector3(self.radius, self.radius, self.radius)
        #TODO: should be done on all components
        if self.surface is not None:
            self.surface.set_scale(scale)
        if self.clouds is not None:
            self.clouds.set_scale(scale)

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

    def get_scale(self):
        if self.surface is not None:
            return self.surface.shape.get_scale()
        else:
            return LVector3d()

    def get_extend(self):
        if self.ring is not None:
            return self.ring.outer_radius
        elif self.surface is not None:
            return self.surface.get_max_radius()
        else:
            return self.get_apparent_radius()

    def get_height_under(self, position):
        if self.surface is not None:
            (x, y, distance) = self.spherical_to_longlat(self.cartesian_to_spherical(position))
            return self.surface.get_height_at(x, y)
        else:
            #print("No surface")
            return self.radius

    def get_normals_under(self, position):
        if self.surface is not None:
            (x, y, distance) = self.spherical_to_longlat(self.cartesian_to_spherical(position))
            vectors = self.surface.get_normals_at(x, y)
        else:
            vectors = (LVector3d.up(), LVector3d.forward(), LVector3d.left())
        sync_frame = SynchroneReferenceFrame(self)
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
    def __init__(self, *args, **kwargs):
        self.albedo = kwargs.pop('albedo', 0.5)
        StellarBody.__init__(self, *args, **kwargs)
        self.sunLight = None

    def is_emissive(self):
        return False

    def get_abs_magnitude(self):
        luminosity = self.get_luminosity() * self.get_phase()
        if luminosity > 0.0:
            return lum_to_abs_mag(luminosity)
        else:
            return 99.0

    def get_luminosity(self):
        if self.star is None or self.distance_to_star is None: return 0.0
        star_power = self.star.get_luminosity()
        area = 4 * pi * self.distance_to_star * self.distance_to_star * 1000 * 1000
        if area > 0.0:
            irradiance = star_power / area
            surface = 4 * pi * self.get_apparent_radius() * self.get_apparent_radius() * 1000 * 1000
            received_energy = irradiance * surface
            reflected_energy = received_energy * self.albedo
            return reflected_energy
        else:
            print("No area")
            return 0.0

    def get_phase(self):
        if self.vector_to_obs is None or self.vector_to_star is None: return 0.0
        angle = self.vector_to_obs.dot(self.vector_to_star)
        phase = (1.0 + angle) / 2.0
        return phase

    def check_cast_shadow_on(self, body):
        position = self.get_local_position()
        body_position = body.get_local_position()
        pa = body_position - position
        distance_vector = pa - self.vector_to_star * self.vector_to_star.dot(pa)
        distance = distance_vector.length()
        projected = self.vector_to_star * self.vector_to_star.dot(body_position)
        face = self.vector_to_star.dot(projected - position)
        return face < 0.0 and distance < self.get_apparent_radius() + body.get_apparent_radius()

    def start_shadows_update(self):
        self.surface.start_shadows_update()
        #TODO: this should be done by looping over components
        if self.clouds is not None:
            self.clouds.start_shadows_update()

    def add_shadow_target(self, target):
        self.surface.add_shadow_target(target.surface)
        if target.clouds is not None:
            self.surface.add_shadow_target(target.clouds)

    def end_shadows_update(self):
        self.surface.end_shadows_update()
        if self.clouds is not None:
            self.clouds.end_shadows_update()

    def create_light(self):
        print("Create light for", self.get_name())
        self.dir_light = DirectionalLight('sunLight')
        self.dir_light.setDirection(LVector3(*-self.vector_to_star))
        self.dir_light.setColor((1, 1, 1, 1))
        self.sunLight = self.context.world.attachNewNode(self.dir_light)
        self.set_light(self.sunLight)

    def update_light(self, camera_pos):
        pos = self.get_local_position() + self.vector_to_star * self.get_extend()
        self.place_pos_only(self.sunLight, pos, camera_pos, self.distance_to_obs, self.vector_to_obs)
        self.dir_light.setDirection(LVector3(*-self.vector_to_star))

    def remove_light(self):
        self.sunLight.remove_node()
        self.sunLight = None
        self.dir_light = None

    def configure_shape(self):
        StellarBody.configure_shape(self)
        self.surface.create_shadows()
        if self.ring is not None and self.surface is not None:
            #TODO: This should be in start_shadow_update...
            self.ring.shadow_caster.add_target(self.surface)
            if self.clouds is not None:
                self.ring.shadow_caster.add_target(self.clouds)
            self.ring.start_shadows_update()
            self.surface.shadow_caster.add_target(self.ring)
            self.ring.end_shadows_update()

    def create_components(self):
        StellarBody.create_components(self)
        if self.sunLight is None:
            self.create_light()
            self.update_shader()

    def update_components(self, camera_pos):
        if self.sunLight is not None:
            self.update_light(camera_pos)

    def remove_components(self):
        if self.sunLight is not None:
            self.remove_light()
            self.update_shader()
        StellarBody.remove_components(self)

class EmissiveBody(StellarBody):
    has_halo = True
    has_resolved_halo = True
    def __init__(self, *args, **kwargs):
        abs_magnitude = kwargs.pop('abs_magnitude', None)
        StellarBody.__init__(self, *args, **kwargs)
        self.abs_magnitude = abs_magnitude

    def is_emissive(self):
        return True

    def get_abs_magnitude(self):
        return self.abs_magnitude

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
        return FlatSurface('surface', shape=shape, appearance=appearance, shader=shader)

class Star(EmissiveBody):
    def __init__(self, names, radius=None, oblateness=None,
                 surface=None, surface_factory=None,
                 orbit=None, rotation=None,
                 abs_magnitude=None, temperature=None, spectral_type=None,
                 atmosphere=None, ring=None, clouds=None, point_color=None,
                 body_class='star'):
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
                self.temperature = self.spectral_type.get_eff_temperature()
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
        self._extend = radius #TODO: Optim for octree
        EmissiveBody.__init__(self, names=names, radius=radius, oblateness=oblateness,
                              surface=surface, surface_factory=surface_factory,
                              orbit=orbit, rotation=rotation,
                              abs_magnitude=abs_magnitude,
                              atmosphere=atmosphere, ring=ring, clouds=clouds, point_color=point_color,
                              body_class=body_class)

class DeepSpaceObject(EmissiveBody):
    has_rotation_axis = False
    has_reference_axis = False
    has_resolved_halo = False
    support_offset_body_center = False

    def __init__(self, name, radius, radius_units=units.Ly,
                 abs_magnitude=None,
                 surface=None,
                 orbit=None, rotation=None,
                 body_class=None, point_color=None,
                 description=''):
        radius = radius * radius_units
        EmissiveBody.__init__(self, name, radius,
                              surface=surface,
                              orbit=orbit, rotation=rotation,
                              abs_magnitude=abs_magnitude,
                              body_class=body_class, point_color=point_color,
                              description=description)

    def get_apparent_radius(self):
        return self.radius

    def get_height_under(self, position):
        return 0.0

    def check_and_update_instance(self, camera_pos, orientation, pointset):
        EmissiveBody.check_and_update_instance(self, camera_pos, orientation, pointset)
        app_magnitude = self.get_app_magnitude()
        self.surface.appearance.set_magnitude(self, self.surface.shape, self.surface.shader, self.abs_magnitude, app_magnitude, self.visible_size)

class SkySphere(VisibleObject):
    def __init__(self, names, shape=None, appearance=None, shader=None, orientation=FixedRotation()):
        #TODO: should be a ShapeObject instead !
        VisibleObject.__init__(self, names)
        self.appearance = appearance
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
