#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2020 Laurent Deru.
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
from panda3d.core import DirectionalLight

from .astro.frame import AbsoluteReferenceFrame
from .foundation import VisibleObject
from .parameters import ParametersGroup
from .shadows import CustomShadowMapShadowCaster
from . import utils

from math import pi
from cosmonium.camera import CameraController

class ShipBase(VisibleObject):
    editable = False
    def __init__(self, name):
        VisibleObject.__init__(self, name)
        self.camera_modes = [CameraController.FIXED]

        self.frame = AbsoluteReferenceFrame()
        self._frame_position = LPoint3d()
        self._frame_rotation = LQuaterniond()

        self._position = LPoint3d()
        self._global_position = LPoint3d()
        self._local_position = LPoint3d()
        self._orientation = LQuaterniond()

        self.camera_distance = 0.0
        self.camera_pos = LPoint3d()
        self.camera_rot = LQuaterniond()

    def add_camera_mode(self, mode):
        if not mode in self.camera_modes:
            self.camera_modes.append(mode)

    def supports_camera_mode(self, mode):
        return mode in self.camera_modes

    def copy(self, other):
        self.frame = other.frame
        self._frame_position = other._frame_position
        self._frame_rotation = other._frame_rotation

    def get_camera_hints(self):
        return {'distance': self.camera_distance,
                'position': self.camera_pos,
                'rotation': self.camera_rot}

    def set_camera_hints(self, camera_distance, camera_pos, camera_rot):
        self.camera_distance = camera_distance
        self.camera_pos = camera_pos
        self.camera_rot = camera_rot

    def set_frame(self, frame):
        #Get position and rotation in the absolute reference frame
        pos = self.get_pos()
        rot = self.get_rot()
        #Update reference frame
        self.frame = frame
        #Set back the position to calculate the position in the new reference frame
        self.set_pos(pos)
        self.set_rot(rot)

    def change_global(self, new_global_pos):
        old_local = self.frame.get_local_position(self._frame_position)
        new_local = (self._global_position - new_global_pos) + old_local
        self._global_position = new_global_pos
        self._frame_position = self.frame.get_rel_position(new_local)
        self.do_update()

    def get_position(self):
        return self._global_position + self.frame.get_local_position(self._frame_position)

    def set_frame_pos(self, position):
        self._frame_position = position

    def get_frame_pos(self):
        return self._frame_position

    def set_frame_rot(self, rotation):
        self._frame_rotation = rotation

    def get_frame_rot(self):
        return self._frame_rotation

    def get_position_of(self, rel_position):
        return self._global_position + self.frame.get_local_position(rel_position)

    def get_rel_position_to(self, position):
        return (self._global_position - position) + self.get_local_position()

    def get_rel_position_of(self, position, local=True):
        if not local:
            position -= self._global_position
        return self.frame.get_rel_position(position)

    def get_rel_rotation_of(self, orientation):
        return self.frame.get_rel_orientation(orientation)

    def set_pos(self, position, local=True):
        if not local:
            position -= self._global_position
        self._frame_position = self.frame.get_rel_position(position)

    def get_pos(self):
        return self.frame.get_local_position(self._frame_position)

    def set_rot(self, orientation):
        self._frame_rotation = self.frame.get_rel_orientation(orientation)

    def get_rot(self):
        return self.frame.get_abs_orientation(self._frame_rotation)

    def do_update(self):
        #TODO: _position should be global + local !
        self._position = self.get_pos()
        self._local_position = self.get_pos()
        self._orientation = self.get_rot()

    def update(self, time, dt):
        self.do_update()

    def turn_back(self):
        new_rot = utils.relative_rotation(self.get_rot(), LVector3d.up(), pi)
        self.set_rot(new_rot)

    def step(self, delta, absolute=True):
        if absolute:
            self.set_pos(self.get_pos() + delta)
        else:
            self._frame_position += delta

    def turn(self, orientation, absolute=True):
        if absolute:
            self.set_rot(orientation)
        else:
            self._frame_rotation = orientation

    def step_turn(self, delta, absolute=True):
        if absolute:
            self.set_rot(delta * self.get_rot())
        else:
            self._frame_rotation = delta * self._frame_rotation

    def calc_look_at(self, target, rel=True, position=None):
        if not rel:
            if position is None:
                position = self.get_pos()
            direction = LVector3d(target - position)
        else:
            direction = LVector3d(target)
        direction.normalize()
        local_direction = self.get_rot().conjugate().xform(direction)
        angle = LVector3d.forward().angleRad(local_direction)
        axis = LVector3d.forward().cross(local_direction)
        if axis.length() > 0.0:
            new_rot = utils.relative_rotation(self.get_rot(), axis, angle)
#         new_rot=LQuaterniond()
#         lookAt(new_rot, direction, LVector3d.up())
        else:
            new_rot = self.get_rot()
        return new_rot, angle

    def set_parent(self, parent):
        pass

    def set_light(self, light):
        pass

    def update_obs(self, observer):
        pass

    def check_visibility(self, pixel_size):
        pass

    def check_settings(self):
        pass

    def check_and_update_instance(self, camera_pos, camera_rot, pointset):
        pass

    def remove_instance(self):
        pass

    def set_state(self, new_state):
        pass

class NoShip(ShipBase):
    def __init__(self):
        ShipBase.__init__(self, "No ship")

    def get_apparent_radius(self):
        return 0.0

class VisibleShip(ShipBase):
    editable = True
    def __init__(self, name, ship_object, radius):
        ShipBase.__init__(self, name)
        self.ship_object = ship_object
        self.radius = radius
        #TODO: Should be refactored with StellarBody !
        self.shown = True
        self.visible = True
        self.resolved = True
        self.oid_color = LColor()
        self.world_body_center_offset = LVector3d()
        self.model_body_center_offset = LVector3d()
        self.light_color = LColor(1, 1, 1, 1)
        self.rel_position = None
        self.scene_rel_position = None
        self.distance_to_obs = None
        self.vector_to_obs = None
        self.vector_to_star = None
        self.star = None
        self.directional_light = None
        self.light_source = None

        self.scene_position = None
        self.scene_distance = None
        self.scene_scale_factor = None
        self.scene_orientation = None

        self.ship_object.set_parent(self)
        self.ship_object.set_scale(LVector3d(self.radius, self.radius, self.radius))

        self.shadow_caster = None
        self.create_own_shadow_caster = True

    def check_settings(self):
        self.ship_object.check_settings()
        if self.shadow_caster is not None:
            self.shadow_caster.check_settings()

    def get_user_parameters(self):
        parameters = self.ship_object.get_user_parameters()
        group = ParametersGroup(self.get_name(), parameters)
        return group

    def update_user_parameters(self):
        self.ship_object.update_user_parameters()

    def get_apparent_radius(self):
        return self.radius

    def get_extend(self):
        return self.radius

    def get_local_position(self):
        return self._local_position

    #TODO: Should be refactored with StellarBody !
    def create_light(self):
        print("Create light for", self.get_name())
        self.directional_light = DirectionalLight('light_source')
        self.directional_light.setDirection(LVector3(*-self.vector_to_star))
        self.directional_light.setColor((1, 1, 1, 1))
        self.light_source = self.context.world.attachNewNode(self.directional_light)
        self.set_light(self.light_source)

    def update_light(self, camera_pos):
        if self.light_source is None: return
        pos = self.get_local_position() + self.vector_to_star * self.get_extend()
        self.place_pos_only(self.light_source, pos, camera_pos, self.distance_to_obs, self.vector_to_obs)
        self.directional_light.setDirection(LVector3(*-self.vector_to_star))

    def remove_light(self):
        self.light_source.remove_node()
        self.light_source = None
        self.directional_light = None

    def update(self, time, dt):
        ShipBase.update(self, time, dt)
        self.ship_object.update(time, dt)

    def update_obs(self, observer):
        self.rel_position = self._local_position - observer._local_position
        self.distance_to_obs = self.rel_position.length()
        self.vector_to_obs = self.rel_position / self.distance_to_obs
        if self.context.nearest_system is not None:
            self.star = self.context.nearest_system.star
            self.vector_to_star = (self.star._local_position - self._local_position).normalized()
            if self.light_source is None:
                self.create_light()
        else:
            self.star = None
            self.vector_to_star = LVector3d.up()
            if self.light_source is not None:
                self.remove_light()
        self.ship_object.update_obs(observer)

    def check_visibility(self, pixel_size):
        self.ship_object.check_visibility(pixel_size)

    def update_shader(self):
        ShipBase.update_shader(self)
        self.ship_object.update_shader()

    def check_and_update_instance(self, camera_pos, camera_rot, pointset):
        self.scene_rel_position = self.rel_position
        self.scene_position, self.scene_distance, self.scene_scale_factor = self.calc_scene_params(self.rel_position, self._position, self.distance_to_obs, self.vector_to_obs)
        self.scene_orientation = self._orientation
        self.ship_object.check_and_update_instance(camera_pos, camera_rot, pointset)
        self.instance = self.ship_object.instance
        self.instance.hide(self.AllCamerasMask)
        self.instance.show(self.NearCameraMask)
        self.instance.show(self.WaterCameraMask)
        self.instance.show(self.ShadowCameraMask)
        self.update_light(camera_pos)
        if self.create_own_shadow_caster:
            if self.shadow_caster is None:
                self.shadow_caster = CustomShadowMapShadowCaster(self, None)
                self.shadow_caster.create()
            self.shadow_caster.update()
            self.ship_object.shadows.start_update()
            self.shadow_caster.add_target(self.ship_object)
            self.ship_object.shadows.end_update()

    def remove_instance(self):
        self.ship_object.remove_instance()
        self.instance = None
        if self.shadow_caster is not None:
            self.shadow_caster.remove()
            self.shadow_caster = None
            self.remove_light()

class ActorShip(VisibleShip):
    pass
