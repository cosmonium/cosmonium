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

from panda3d.core import LPoint3d, LVector3d, LVector3, LQuaterniond, LColor

from .foundation import CompositeObject, ObjectLabel, LabelledObject
from .annotations import ReferenceAxis, RotationAxis, Orbit
from .astro.frame import SynchroneReferenceFrame
from .astro.orbits import FixedOrbit, FixedPosition
from .astro.rotations import UnknownRotation
from .astro.astro import abs_to_app_mag
from .bodyclass import bodyClasses
from .catalogs import objectsDB
from .parameters import ParametersGroup
from . import settings
from .settings import smallest_glare_mag
from .utils import mag_to_scale, srgb_to_linear

from math import pi, asin, atan2, sin, cos

class StellarBodyLabel(ObjectLabel):
    def get_oid_color(self):
        return self.parent.oid_color

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

    def update_instance(self, camera_pos, camera_rot):
        body = self.parent
        if body.is_emissive() and (not body.resolved or body.background):
            if body.scene_position != None:
                self.instance.setPos(*body.scene_position)
                scale = abs(self.context.observer.pixel_size * body.get_label_size() * body.scene_distance)
            else:
                scale = 0.0
        else:
            offset = body.get_apparent_radius() * 1.01
            rel_front_pos = body.rel_position - camera_rot.xform(LPoint3d(0, offset, 0))
            vector_to_obs = LVector3d(-rel_front_pos)
            distance_to_obs = vector_to_obs.length()
            vector_to_obs /= distance_to_obs
            position, distance, scale_factor = self.calc_scene_params(rel_front_pos, rel_front_pos, distance_to_obs, vector_to_obs)
            self.instance.setPos(*position)
            scale = abs(self.context.observer.pixel_size * body.get_label_size() * distance)
        self.look_at.set_pos(LVector3(*(camera_rot.xform(LVector3d.forward()))))
        self.label_instance.look_at(self.look_at, LVector3(), LVector3(*(camera_rot.xform(LVector3d.up()))))
        self.instance.set_color_scale(LColor(self.fade, self.fade, self.fade, 1.0))
        if scale < 1e-7:
            print("Label too far", self.get_name())
            scale = 1e-7
        self.instance.setScale(scale)

class FixedOrbitLabel(StellarBodyLabel):
    def check_visibility(self, pixel_size):
        #TODO: Should be refactored !
        if hasattr(self.parent, "primary") and self.parent.resolved and (self.parent.primary is None or (self.parent.primary.label is not None and self.parent.primary.label.visible)):
            self.visible = False
            return
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
    background = False
    nb_update = 0
    nb_obs = 0
    nb_visibility = 0
    nb_instance = 0

    def __init__(self, names, source_names, orbit=None, rotation=None, body_class=None, point_color=None, description=''):
        LabelledObject.__init__(self, names)
        self.source_names = source_names
        self.description = description
        self.system = None
        self.body_class = body_class
        if orbit is None:
            orbit = FixedOrbit()
        self.orbit = orbit
        if rotation is None:
            rotation = UnknownRotation()
        self.rotation = rotation
        if point_color is None:
            point_color = LColor(1.0, 1.0, 1.0, 1.0)
        self.point_color = srgb_to_linear(point_color)
        self.abs_magnitude = 99.0
        self.oid = None
        self.oid_color = None
        #Flags
        self.visible = False
        self.resolved = False
        self.in_view = False
        self.selected = False
        self.update_id = 0
        self.visibility_override = False
        #Cached values
        self._position = LPoint3d()
        self._global_position = LPoint3d()
        self._local_position = LPoint3d()
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
        self._height_under = 0.0
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
        #TODO: This is temporary until v0.3.x
        self.create_orbit_object()
        objectsDB.add(self)

    def is_system(self):
        return False

    def check_settings(self):
        LabelledObject.check_settings(self)
        if self.body_class is None:
            print("No class for", self.get_name())
            return
        self.set_shown(bodyClasses.get_show(self.body_class))

    def get_user_parameters(self):
        group = ParametersGroup(self.get_name())
        parameters = []
        if isinstance(self.orbit, FixedOrbit) and self.system is not None:
            orbit = self.system.orbit
        else:
            orbit = self.orbit
        general_group = ParametersGroup(_('General'))
        general_group.add_parameter(orbit.get_user_parameters())
        general_group.add_parameter(self.rotation.get_user_parameters())
        group.add_parameter(general_group)
        for component in self.components:
            component_group = component.get_user_parameters()
            if component_group is not None:
                group.add_parameter(component_group)
        return group

    def update_user_parameters(self):
        LabelledObject.update_user_parameters(self)
        if isinstance(self.orbit, FixedOrbit) and self.system is not None:
            self.system.orbit.update_user_parameters()
            if self.system.orbit_object is not None:
                self.system.orbit_object.update_user_parameters()
        else:
            self.orbit.update_user_parameters()
            if self.orbit_object is not None:
                self.orbit_object.update_user_parameters()
        self.rotation.update_user_parameters()

    def get_fullname(self, separator='/'):
        if hasattr(self, "primary") and self.primary is not None:
            name = self.primary.get_friendly_name()
        else:
            name = self.get_friendly_name()
        if not hasattr(self.parent, "primary") or self.parent.primary is not self:
            fullname = self.parent.get_fullname(separator)
        else:
            fullname = self.parent.parent.get_fullname(separator)
        if fullname != '':
            return fullname + separator + name
        else:
            return name

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
        self.orbit.set_body(self)
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
        for name in self.source_names:
            if name.upper() == name_up:
                return True
        return False

    def set_selected(self, selected):
        self.selected = selected
        if self.orbit_object:
            self.orbit_object.set_selected(selected)
        else:
            if self.parent:
                self.parent.set_selected(selected)

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
        return self._local_position

    def get_position(self):
        return self.get_global_position() + self.get_local_position()

    def get_rel_position_to(self, position):
        return (self.get_global_position() - position) + self.get_local_position()

    def get_abs_rotation(self):
        return self._orientation

    def get_equatorial_rotation(self):
        return self._equatorial

    def get_sync_rotation(self):
        return self._orientation

    def frame_cartesian_to_spherical(self, position):
        distance = position.length()
        if distance > 0:
            theta = asin(position[2] / distance)
            if position[0] != 0.0:
                phi = atan2(position[1], position[0])
                #Offset phi by 180 deg with proper wrap around
                #phi = (phi + pi + pi) % (2 * pi) - pi
            else:
                phi = 0.0
        else:
            phi = 0.0
            theta = 0.0
        return (phi, theta, distance)

    def cartesian_to_spherical(self, position):
        sync_frame = SynchroneReferenceFrame(self)
        rel_position = sync_frame.get_rel_position(position)
        return self.frame_cartesian_to_spherical(rel_position)

    def spherical_to_frame_cartesian(self, position):
        (phi, theta, distance) = position
        #Offset phi by 180 deg with proper wrap around
        #phi = (phi + pi + pi) % (2 * pi) - pi
        rel_position = LPoint3d(cos(theta) * cos(phi), cos(theta) * sin(phi), sin(theta))
        rel_position *= distance
        return rel_position

    def spherical_to_cartesian(self, position):
        rel_position = self.spherical_to_frame_cartesian(position)
        sync_frame = SynchroneReferenceFrame(self)
        position = sync_frame.get_local_position(rel_position)
        return position

    def spherical_to_xy(self, position):
        (phi, theta, distance) = position
        x = phi / pi / 2 + 0.5
        y = theta / pi + 0.5
        return (x, y, distance)

    def xy_to_spherical(self, position):
        (x, y, distance) = position
        phi = (x - 0.5) * pi / 2
        tetha = (y - 0.5) * pi
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

    def set_visibility_override(self, override):
        if override == self.visibility_override: return
        if override:
            self.visibility_override = True
            if self.system is not None:
                self.system.set_visibility_override(override)
        else:
            self.visibility_override = False
            if self.system is not None:
                self.system.set_visibility_override(override)
            #Force recheck of visibility or the object will be instanciated in create_or_update_instance()
            self.check_visibility(self.context.observer.pixel_size)

    def first_update(self, time):
        self.update(time, 0)

    def update(self, time, dt):
        StellarObject.nb_update += 1
        self._orientation = self.rotation.get_rotation_at(time)
        self._equatorial = self.rotation.get_equatorial_orientation_at(time)
        self._local_position = self.orbit.get_position_at(time)
        self._global_position = self.parent._global_position + self.orbit.get_global_position_at(time)
        self._position = self._global_position + self._local_position
        if self.star is not None:
            (self.vector_to_star, self.distance_to_star) = self.calc_local_distance_to(self.star.get_local_position())
        CompositeObject.update(self, time, dt)
        self.update_frozen = not self.resolved and not (self.orbit.dynamic or self.rotation.dynamic)

    def start_shadows_update(self):
        pass

    def end_shadows_update(self):
        pass

    def first_update_obs(self, observer):
        self.update_obs(observer)

    def update_obs(self, observer):
        StellarObject.nb_obs += 1
        global_delta = self._global_position - observer.camera_global_pos
        local_delta = self._local_position - observer._position
        self.rel_position = global_delta + local_delta
        length = self.rel_position.length()
        self.vector_to_obs = -self.rel_position / length
        self.distance_to_obs = length
        if self.resolved:
            self._height_under = self.get_height_under(observer._position)
        else:
            self._height_under = self.get_apparent_radius()
        CompositeObject.update_obs(self, observer)

    def check_visibility(self, pixel_size):
        StellarObject.nb_visibility += 1
        if self.distance_to_obs > 0.0:
            self.visible_size = self._extend / (self.distance_to_obs * pixel_size)
        else:
            self.visible_size = 0.0
        self._app_magnitude = self.get_app_magnitude()
        self.resolved = self.visible_size > settings.min_body_size
        if not self.visibility_override:
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
        else:
            self.visible = True
        if not self.virtual_object and self.resolved and self.in_view:
            self.context.add_visible(self)
        LabelledObject.check_visibility(self, pixel_size)

    def check_and_update_instance(self, camera_pos, camera_rot, pointset):
        StellarObject.nb_instance += 1
        if self.support_offset_body_center and self.visible and self.resolved and settings.offset_body_center:
            self.scene_rel_position = self.rel_position + self.vector_to_obs * self._height_under
            distance_to_obs = self.distance_to_obs - self._height_under
        else:
            self.scene_rel_position = self.rel_position
            distance_to_obs = self.distance_to_obs
        self.scene_position, self.scene_distance, self.scene_scale_factor = self.calc_scene_params(self.scene_rel_position, self._position, distance_to_obs, self.vector_to_obs)
        self.scene_orientation = self.get_abs_rotation()
        if self.label is None:
            self.create_label()
            self.label.check_settings()
        if self.visible:
            if not self.init_annotations:
                self.create_annotations()
                self.check_settings()
            if self.resolved:
                if not self.init_components:
                    self.create_components()
                    self.check_settings()
                if self.support_offset_body_center and settings.offset_body_center:
                    self.world_body_center_offset = -self.vector_to_obs * self._height_under * self.scene_scale_factor
                    self.model_body_center_offset = self.scene_orientation.conjugate().xform(-self.vector_to_obs) * self._height_under
                    if self._height_under != 0:
                        scale = self.surface.get_scale()
                        self.model_body_center_offset[0] /= scale[0]
                        self.model_body_center_offset[1] /= scale[1]
                        self.model_body_center_offset[2] /= scale[2]
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
            if self.init_components:
                self.remove_components()
        CompositeObject.check_and_update_instance(self, camera_pos, camera_rot, pointset)

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
            size = max(settings.min_point_size, settings.min_point_size + scale * settings.mag_pixel_scale)
            pointset.add_point(self.scene_position, color, size, self.oid_color)
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
        self.context.haloset.add_point(LVector3(*position), self.point_color, size, self.oid_color)

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
