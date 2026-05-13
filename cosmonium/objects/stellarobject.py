#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2025 Laurent Deru.
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


import re

from panda3d.core import LColor, LVector3d

from ..bodyclass import bodyClasses
from ..catalogs import objectsDB
from ..engine.anchors import CartesianAnchor
from ..engine.anchors import DynamicStellarAnchor
from ..foundation import CompositeObject
from ..scene.sceneanchor import SceneAnchor
from ..utils import srgb_to_linear
from .. import settings


class StellarObject:
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
    stellar_object = True
    nb_update = 0
    nb_obs = 0
    nb_visibility = 0
    nb_instance = 0
    to_alphanum = re.compile('[^a-zA-Z0-9]')

    def __init__(
        self,
        names,
        orbit=None,
        rotation=None,
        frame=None,
        body_class=None,
        point_color=None,
    ):
        self.body_class = body_class
        if point_color is None:
            point_color = LColor(1.0, 1.0, 1.0, 1.0)
        point_color = srgb_to_linear(point_color)
        # if not (orbit.dynamic or rotation.dynamic):
        #    self.anchor = FixedStellarAnchor(self, orbit, rotation, point_color)
        # else:
        self.anchor = self.create_anchor(self.anchor_class, orbit, rotation, frame, point_color, names)
        self.anchor.scene_anchor = SceneAnchor(
            self.get_ascii_name() + '-scene-anchor',
            self.anchor,
            self.support_offset_body_center,
            LColor(),
            background=self.background,
            virtual_object=self.virtual_object,
            spread_object=self.spread_object,
        )
        self.oid = None
        self.oid_color = None
        # Flags
        self.selected = False
        self.focused = False
        # Scene parameters
        self.light_color = (1.0, 1.0, 1.0, 1.0)
        # Components
        self.init_components = False
        objectsDB.add(self)
        # TODO: Should be done properly
        self.anchor.scene_anchor.oid_color = self.oid_color

        self.shown = True
        self.parent = None
        self.lights = None

        self.components = CompositeObject(self.get_ascii_name())
        self.components.set_scene_anchor(self.anchor.scene_anchor)

    def get_names(self):
        return self.anchor.get_names()

    def set_names(self, names):
        self.anchor.set_names(names)

    def get_source_names(self):
        return self.anchor.get_source_names()

    def get_name(self):
        return self.anchor.get_name()

    def get_c_name(self):
        return self.anchor.get_c_name()

    def get_ascii_name(self):
        name = self.to_alphanum.sub('x', self.get_c_name())
        if not name[0].isalpha():
            name = 'x' + name
        return name

    def get_description(self):
        return self.anchor.get_description()

    def set_description(self, description):
        self.anchor.set_description(description)

    @property
    def visible(self):
        return self.anchor.visible

    @property
    def scene_anchor(self):
        return self.anchor.scene_anchor

    def set_parent(self, parent):
        self.parent = parent

    def set_lights(self, lights):
        if self.lights is not None:
            self.lights.remove_all()
        self.lights = lights
        self.components.set_lights(lights)

    def create_anchor(self, anchor_class, orbit, rotation, frame, point_color, names):
        if rotation is None and orbit is None:
            return CartesianAnchor(anchor_class, self, frame, point_color, names)
        else:
            return DynamicStellarAnchor(anchor_class, self, orbit, rotation, point_color, names)

    def is_system(self):
        return self.anchor.is_system()

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

    def get_fullname(self, separator='/'):
        return self.anchor.get_fullname(separator)

    def create_components(self):
        pass

    def update_components(self, camera_pos):
        pass

    def remove_components(self):
        pass

    def set_system(self, system):
        self.anchor.set_system(system.anchor)

    def set_body_class(self, body_class):
        self.body_class = body_class

    def set_orbit(self, orbit):
        self.anchor.orbit = orbit

    def set_rotation(self, rotation):
        self.anchor.rotation = rotation

    def set_focused(self, focused):
        self.focused = focused

    def set_selected(self, selected):
        self.selected = selected

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

    def get_point_under(self, position):
        return self.anchor.get_local_position()

    def get_tangent_plane_under(self, position):
        vectors = (LVector3d.right(), LVector3d.forward(), LVector3d.up())
        return vectors

    def set_visibility_override(self, override):
        if override == self.anchor.visibility_override:
            return
        if override:
            self.anchor.visibility_override = True
            if self.anchor.has_system():
                self.anchor.system.body.set_visibility_override(override)
        else:
            self.anchor.visibility_override = False
            if self.anchor.has_system():
                self.anchor.system.body.set_visibility_override(override)
            # Force recheck of visibility or the object will be instanciated in create_or_update_instance()
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

    def check_and_create_instance(self, scene_manager, camera_pos, camera_rot):
        self.components.check_and_create_instance(scene_manager, camera_pos, camera_rot)

    def check_and_update_instance(self, scene_manager, camera_pos, camera_rot):
        StellarObject.nb_instance += 1
        if self.lights is not None:
            self.lights.update_instances(camera_pos)
        self.update_components(camera_pos)
        self.components.check_and_update_instance(scene_manager, camera_pos, camera_rot)
