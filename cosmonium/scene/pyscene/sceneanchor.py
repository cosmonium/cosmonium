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


from panda3d.core import LPoint3, LPoint3d, LVector3d, LQuaternion, NodePath

from ... import settings

from math import log

class SceneAnchor:
    anchor_name = 'scene-anchor'
    def __init__(self, anchor, support_offset_body_center, oid_color, apply_orientation=False, background=False, virtual_object=False):
        self.anchor = anchor
        self.support_offset_body_center = support_offset_body_center
        self.oid_color = oid_color
        self.apply_orientation = apply_orientation
        self.background = background
        self.virtual_object = virtual_object
        self.instance = None
        self.shifted_instance = None
        self.unshifted_instance = None
        self.scene_position = LPoint3d()
        self.scene_orientation = LQuaternion()
        self.scene_distance = 0.0
        self.scene_scale_factor = 0.0
        self.scene_rel_position = LPoint3d()
        self.world_body_center_offset = LVector3d()
        self.scene_body_center_offset = LVector3d()

    def create_instance(self, scene_manager):
        if self.instance is None:
            self.instance = NodePath(self.anchor_name)
            scene_manager.attach_new_anchor(self.instance)
            self.shifted_instance = self.instance.attach_new_node('shifted-anchor')
            self.unshifted_instance = self.instance.attach_new_node('unshifted-anchor')

    def remove_instance(self):
        if self.instance is not None:
            self.instance.remove_node()
            self.instance = None
            self.shifted_instance = None
            self.unshifted_instance = None

    def update(self, scene_manager):
        anchor = self.anchor
        if self.support_offset_body_center and anchor.visible and anchor.resolved and settings.offset_body_center:
            self.world_body_center_offset = -self.anchor.vector_to_obs * self.anchor._height_under * self.scene_scale_factor
            self.scene_body_center_offset = -self.anchor.vector_to_obs * self.anchor._height_under
            self.scene_rel_position = anchor.rel_position - self.scene_body_center_offset
            distance_to_obs = anchor.distance_to_obs - anchor._height_under
            self.scene_position, self.scene_distance, self.scene_scale_factor = self.calc_scene_params(scene_manager, self.scene_rel_position, anchor._position, distance_to_obs, anchor.vector_to_obs)
            if self.unshifted_instance is not None:
                self.unshifted_instance.set_pos(*self.scene_body_center_offset)
        else:
            self.scene_rel_position = anchor.rel_position
            distance_to_obs = anchor.distance_to_obs
            self.scene_position, self.scene_distance, self.scene_scale_factor = self.calc_scene_params(scene_manager, self.scene_rel_position, anchor._position, distance_to_obs, anchor.vector_to_obs)
            if self.unshifted_instance is not None:
                self.unshifted_instance.set_pos(LPoint3())
        if self.instance is not None:
            self.instance.set_pos(*self.scene_position)
            if self.apply_orientation:
                self.scene_orientation = LQuaternion(*anchor._orientation)
                self.instance.set_quat(self.scene_orientation)
            self.instance.set_scale(self.scene_scale_factor)

    @classmethod
    def calc_scene_params(cls, scene_manager, rel_position, abs_position, distance_to_obs, vector_to_obs):
        if settings.camera_at_origin:
            obj_position = rel_position
        else:
            obj_position = abs_position
        midPlane = scene_manager.midPlane
        distance_to_obs /= scene_manager.scale
        if not settings.use_depth_scaling or distance_to_obs <= midPlane:
            position = obj_position / scene_manager.scale
            distance = distance_to_obs
            scale_factor = 1.0 / scene_manager.scale
        elif settings.use_inv_scaling:
            not_scaled = -vector_to_obs * midPlane
            scaled_distance = midPlane * (1 - midPlane / distance_to_obs)
            scaled = -vector_to_obs * scaled_distance
            position = not_scaled + scaled
            distance = midPlane + scaled_distance
            ratio = distance / distance_to_obs
            scale_factor = ratio / scene_manager.scale
        elif settings.use_log_scaling:
            not_scaled = -vector_to_obs * midPlane
            scaled_distance = midPlane * (1 - log(midPlane / distance_to_obs + 1, 2))
            scaled = -vector_to_obs * scaled_distance
            position = not_scaled + scaled
            distance = midPlane + scaled_distance
            ratio = distance / distance_to_obs
            scale_factor = ratio / scene_manager.scale
        return position, distance, scale_factor

class AbsoluteSceneAnchor(SceneAnchor):
    anchor_name = 'static-anchor'
    def __init__(self, anchor):
        SceneAnchor.__init__(self, anchor, False, None)

    def update(self, scene_manager):
        if settings.camera_at_origin:
            self.scene_position = self.anchor.rel_position / scene_manager.scale
            self.instance.set_pos(*self.scene_position)
        self.scene_scale_factor = 1.0 / scene_manager.scale
        self.instance.set_scale(self.scene_scale_factor)

class ObserverSceneAnchor(SceneAnchor):
    anchor_name = 'observer-anchor'
    def __init__(self, anchor, background=False):
        SceneAnchor.__init__(self, anchor, False, None, background=background)

    def update(self, scene_manager):
        if not settings.camera_at_origin:
            self.scene_position = self.anchor._position / scene_manager.scale
            self.instance.set_pos(*self.scene_position)
        self.scene_scale_factor = 1.0 / scene_manager.scale
        self.instance.set_scale(self.scene_scale_factor)

class SceneAnchorCollection(list):
    def add_scene_anchor(self, scene_anchor):
        self.append(scene_anchor)
