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

from panda3d.core import LPoint3d, LQuaterniond, LColor

from ..foundation import BaseObject
from .. import settings

class AnchorBase():
    def __init__(self, body, point_color):
        self.body = body
        #TODO: To remove
        if point_color is None:
            point_color = LColor(1.0, 1.0, 1.0, 1.0)
        self.point_color = point_color
        self.parent = None
        #Flags
        self.visible = False
        self.visibility_override = False
        self.resolved = False
        self.update_id = 0
        self.update_frozen = False
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
        self.visible_size = 0.0
        self.scene_position = None
        self.scene_orientation = None
        self.scene_scale_factor = None

    def calc_global_distance_to(self, position):
        direction = self.get_position() - position
        length = direction.length()
        return (direction / length, length)

    def calc_local_distance_to(self, position):
        direction = position - self._local_position
        length = direction.length()
        return (direction / length, length)

    def update(self, time):
        pass

    def update_simple(self, time):
        self.update(time)

    def update_observer(self, observer, frustum, camera_global_position, camera_local_position, pixel_size):
        pass

    def update_observer_simple(self, observer, frustum, camera_global_position, camera_local_position, pixel_size):
        self.update_observer(observer, frustum, camera_global_position, camera_local_position, pixel_size)

    def update_and_update_observer(self, time, observer, frustum, camera_global_position, camera_local_position, pixel_size):
        self.update(time)
        self.update_observer(observer, frustum, camera_global_position, camera_local_position, pixel_size)

    def update_and_update_observer_simple(self, time, observer, frustum, camera_global_position, camera_local_position, pixel_size):
        self.update_simple(time)
        self.update_observer_simple(observer, frustum, camera_global_position, camera_local_position, pixel_size)

    def update_scene(self):
        pass

class CartesianAnchor(AnchorBase):
    pass

class StellarAnchor(AnchorBase):
    def __init__(self, body, orbit, rotation, point_color):
        AnchorBase.__init__(self, body, point_color)
        self.orbit = orbit
        self.rotation = rotation
        #TODO: Should be done properly
        orbit.body = body
        rotation.body = body
        self.star = None

    def update(self, time):
        self._orientation = self.rotation.get_rotation_at(time)
        self._equatorial = self.rotation.get_equatorial_orientation_at(time)
        self._local_position = self.orbit.get_position_at(time)
        self._global_position = self.body.parent.anchor._global_position + self.orbit.get_global_position_at(time)
        self._position = self._global_position + self._local_position
        if self.star is not None:
            (self.vector_to_star, self.distance_to_star) = self.calc_local_distance_to(self.star.get_local_position())

    def update_observer(self, observer, frustum, camera_global_position, camera_local_position, pixel_size):
        global_delta = self._global_position - camera_global_position
        local_delta = self._local_position - camera_local_position
        rel_position = global_delta + local_delta
        distance_to_obs = rel_position.length()
        vector_to_obs = -rel_position / distance_to_obs
        if distance_to_obs > 0.0:
            visible_size = self._extend / (distance_to_obs * pixel_size)
        else:
            visible_size = 0.0
        self._app_magnitude = self.body.get_app_magnitude()
        radius = self._extend
        if self.visibility_override:
            resolved = visible_size > settings.min_body_size
            visible = True
        elif distance_to_obs > radius:
            in_view = frustum.is_sphere_in(rel_position, radius)
            resolved = visible_size > settings.min_body_size
            visible = in_view and (visible_size > 1.0 or self._app_magnitude < settings.lowest_app_magnitude)
        else:
            #We are in the object
            resolved = True
            visible = True
        if resolved:
            self._height_under = self.body.get_height_under(camera_local_position)
        else:
            self._height_under = self.body.get_apparent_radius()
        self.rel_position = rel_position
        self.vector_to_obs = vector_to_obs
        self.distance_to_obs = distance_to_obs
        self.visible = visible
        self.resolved = resolved
        self.visible_size = visible_size

    def update_scene(self):
        if self.body.support_offset_body_center and self.visible and self.resolved and settings.offset_body_center:
            self.scene_rel_position = self.rel_position + self.vector_to_obs * self._height_under
            distance_to_obs = self.distance_to_obs - self._height_under
        else:
            self.scene_rel_position = self.rel_position
            distance_to_obs = self.distance_to_obs
        self.scene_position, self.scene_distance, self.scene_scale_factor = BaseObject.calc_scene_params(self.scene_rel_position, self._position, distance_to_obs, self.vector_to_obs)
        self.scene_orientation = self._orientation

class FixedStellarAnchor(StellarAnchor):
    def __init__(self, body, orbit, rotation, point_color):
        StellarAnchor.__init__(self, body, orbit, rotation, point_color)
        #self.update_frozen = True
        #self.update(0)

class DynamicStellarAnchor(StellarAnchor):
    pass

class SystemAnchor(DynamicStellarAnchor):
    def __init__(self, body, orbit, rotation, point_color):
        DynamicStellarAnchor.__init__(self, body, orbit, rotation, point_color)
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def remove_child(self, child):
        try:
            self.children.remove(child)
        except ValueError:
            pass

    def update_and_update_observer(self, time, observer, frustum, camera_global_position, camera_local_position, pixel_size):
        DynamicStellarAnchor.update_and_update_observer(self, time, observer, frustum, camera_global_position, camera_local_position, pixel_size)
        if not self.visible or not self.resolved: return
        for child in self.children:
            child.update_and_update_observer(time, observer, frustum, camera_global_position, camera_local_position, pixel_size)

    def update_and_update_observer_children(self, time, observer, frustum, camera_global_position, camera_local_position, pixel_size):
        if not self.visible or not self.resolved: return
        for child in self.children:
            child.update_and_update_observer(time, observer, frustum, camera_global_position, camera_local_position, pixel_size)

    def update_scene(self):
        DynamicStellarAnchor.update_scene(self)
        if not self.visible or not self.resolved: return
        for child in self.children:
            child.update_scene()
