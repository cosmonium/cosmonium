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


from panda3d.core import LColor

from ..foundation import CompositeObject
from ..namedobject import NamedObject
from ..components.annotations.body_label import StellarBodyLabel, FixedOrbitLabel
from ..components.annotations.reference_axes import ReferenceAxes
from ..components.annotations.rotation_axis import RotationAxis
from ..components.annotations.orbit import Orbit
from ..components.elements.halo import Halo
from ..engine.anchors import DynamicStellarAnchor
from ..scene.sceneanchor import SceneAnchor
from ..astro.orbits import FixedPosition
from ..bodyclass import bodyClasses
from ..catalogs import objectsDB
from ..parameters import ParametersGroup
from .. import settings
from ..utils import srgb_to_linear


class StellarObject(NamedObject):
    context = None
    anchor_class = 0
    has_rotation_axis = False
    has_reference_axis = False
    has_orbit = True
    has_halo = False
    has_resolved_halo = False
    virtual_object = False
    spread_object = False
    support_offset_body_center = True
    allow_scattering = False
    background = False
    nb_update = 0
    nb_obs = 0
    nb_visibility = 0
    nb_instance = 0

    def __init__(self, names, source_names, orbit=None, rotation=None, body_class=None, point_color=None, description=''):
        NamedObject.__init__(self, names, source_names, description)
        self.system = None
        self.body_class = body_class
        if point_color is None:
            point_color = LColor(1.0, 1.0, 1.0, 1.0)
        point_color = srgb_to_linear(point_color)
        #if not (orbit.dynamic or rotation.dynamic):
        #    self.anchor = FixedStellarAnchor(self, orbit, rotation, point_color)
        #else:
        self.anchor = self.create_anchor(self.anchor_class, orbit, rotation, point_color)
        self.scene_anchor = SceneAnchor(self.anchor, self.support_offset_body_center, LColor(),
                                        background=self.background, virtual_object=self.virtual_object,
                                        spread_object=self.spread_object)
        self.oid = None
        self.oid_color = None
        #Flags
        self.selected = False
        #Scene parameters
        self.light_color = (1.0, 1.0, 1.0, 1.0)
        #Components
        self.orbit_object = None
        self.rotation_axis = None
        self.reference_axes = None
        self.resolved_halo = None
        self.init_components = False
        objectsDB.add(self)
        #TODO: Should be done properly
        self.scene_anchor.oid_color = self.oid_color

        self.shown = True
        self.visible = False
        self.parent = None
        self.lights = None

        self.components = CompositeObject(self.get_ascii_name())
        self.components.set_scene_anchor(self.scene_anchor)

    def set_parent(self, parent):
        self.parent = parent

    def set_lights(self, lights):
        if self.lights is not None:
            self.lights.remove_all()
        self.lights = lights
        self.components.set_lights(lights)

    def create_anchor(self, anchor_class, orbit, rotation, point_color):
        return DynamicStellarAnchor(anchor_class, self, orbit, rotation, point_color)

    def is_system(self):
        return False

    def check_settings(self):
        self.components.check_settings()
        if self.body_class is None:
            print("No class for", self.get_name())
            return
        self.set_shown(bodyClasses.get_show(self.body_class))

    def set_shown(self, new_shown_status):
        if new_shown_status != self.shown:
            if new_shown_status:
                self.show()
            else:
                self.hide()

    def show(self):
        self.shown = True

    def hide(self):
        self.shown = False

    def get_user_parameters(self):
        group = ParametersGroup(self.get_name())
        parameters = []
        if isinstance(self.orbit, FixedPosition) and self.system is not None:
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
        self.components.update_user_parameters()
        if isinstance(self.orbit, FixedPosition) and self.system is not None:
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
            name = self.primary.get_c_name()
        else:
            name = self.get_c_name()
        if not hasattr(self.parent, "primary") or self.parent.primary is not self:
            fullname = self.parent.get_fullname(separator)
        else:
            fullname = self.parent.parent.get_fullname(separator)
        if fullname != '':
            return fullname + separator + name
        else:
            return name

    def create_label_instance(self):
        if isinstance(self.anchor.orbit, FixedPosition):
            return FixedOrbitLabel(self.get_ascii_name() + '-label', self)
        else:
            return StellarBodyLabel(self.get_ascii_name() + '-label', self)

    def get_description(self):
        return self.description

    def create_components(self):
        if self.has_rotation_axis:
            self.rotation_axis = RotationAxis(self)
            self.components.add_component(self.rotation_axis)
        if self.has_reference_axis:
            self.reference_axes = ReferenceAxes(self)
            self.components.add_component(self.reference_axes)
        if not settings.use_pbr and self.has_resolved_halo:
            self.resolved_halo = Halo(self)
            self.components.add_component(self.resolved_halo)

    def update_components(self, camera_pos):
        pass

    def remove_components(self):
        self.components.remove_component(self.rotation_axis)
        self.rotation_axis = None
        self.components.remove_component(self.reference_axes)
        self.reference_axes = None
        self.components.remove_component(self.resolved_halo)
        self.resolved_halo = None

    def set_system(self, system):
        self.system = system

    def set_body_class(self, body_class):
        self.body_class = body_class

    def create_orbit_object(self):
        if self.orbit_object is None and self.anchor.orbit.is_dynamic():
            self.orbit_object = Orbit(self)
            self.orbit_object.check_settings()

    def remove_orbit_object(self):
        if self.orbit_object is not None:
            self.orbit_object.remove_instance()
            self.orbit_object = None

    def set_orbit(self, orbit):
        if self.orbit_object is not None:
            self.remove_orbit_object()
            recreate = True
        else:
            recreate = False
        self.anchor.orbit = orbit
        if recreate:
            self.create_orbit_object()

    def set_rotation(self, rotation):
        self.anchor.rotation = rotation

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

    def get_bounding_radius(self):
        return self.get_apparent_radius()

    def get_abs_magnitude(self):
        return self.anchor.get_absolute_magnitude()

    def get_app_magnitude(self):
        return self.anchor.get_apparent_magnitude()

    def get_point_radiance(self, distance):
        return self.anchor.get_point_radiance(distance)

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

    def set_visibility_override(self, override):
        if override == self.anchor.visibility_override: return
        if override:
            self.anchor.visibility_override = True
            if self.system is not None:
                self.system.set_visibility_override(override)
        else:
            self.anchor.visibility_override = False
            if self.system is not None:
                self.system.set_visibility_override(override)
            #Force recheck of visibility or the object will be instanciated in create_or_update_instance()
            self.check_visibility(self.context.observer.anchor.frustum, self.context.observer.anchor.pixel_size)

    def update_obs(self, observer):
        self.components.update_obs(observer)

    def check_visibility(self, frustum, pixel_size):
        self.components.check_visibility(frustum, pixel_size)

    def update_lod(self, frustum, pixel_size):
        self.components.update_lod(frustum, pixel_size)

    def on_resolved(self, scene_manager):
        if not self.init_components:
            self.create_components()
            self.components.visible = True
            self.check_settings()
            self.init_components = True

    def on_point(self, scene_manager):
        if self.init_components:
            self.components.remove_instance()
            self.remove_components()
            self.init_components = False

    def check_and_update_instance(self, scene_manager, camera_pos, camera_rot):
        StellarObject.nb_instance += 1
        if self.lights is not None:
            self.lights.update_instances(camera_pos)
        self.update_components(camera_pos)
        self.components.check_and_update_instance(scene_manager, camera_pos, camera_rot)

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
        if self.reference_axes:
            self.reference_axes.show()

    def hide_reference_axis(self):
        if self.reference_axes:
            self.reference_axes.hide()

    def toggle_reference_axis(self):
        if self.reference_axes:
            self.reference_axes.toggle_shown()

    def show_orbit(self):
        if self.orbit_object:
            self.orbit_object.show()

    def hide_orbit(self):
        if self.orbit_object:
            self.orbit_object.hide()

    def toggle_orbit(self):
        if self.orbit_object:
            self.orbit_object.toggle_shown()
