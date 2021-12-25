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


from panda3d.core import LPoint3d, LVector3d, LVector3, LQuaterniond, LColor
from panda3d.core import DirectionalLight

from .sceneworld import CartesianWorld
from .camera import CameraController
from .parameters import ParametersGroup
from .shadows import CustomShadowMapShadowCaster

class ShipBase(CartesianWorld):
    editable = False
    orbit_rot_camera = True
    def __init__(self, name):
        CartesianWorld.__init__(self, name)
        self.camera_modes = [CameraController.FIXED, CameraController.TRACK]

        self.camera_distance = 0.0
        self.camera_pos = LPoint3d()
        self.camera_rot = LQuaterniond()

    def add_camera_mode(self, mode):
        if not mode in self.camera_modes:
            self.camera_modes.append(mode)

    def supports_camera_mode(self, mode):
        return mode in self.camera_modes

    def get_camera_hints(self):
        return {'distance': self.camera_distance,
                'position': self.camera_pos,
                'rotation': self.camera_rot}

    def set_camera_hints(self, camera_distance, camera_pos, camera_rot):
        self.camera_distance = camera_distance
        self.camera_pos = camera_pos
        self.camera_rot = camera_rot

    def set_state(self, new_state):
        pass

class NoShip(ShipBase):
    virtual_object = True
    def __init__(self):
        ShipBase.__init__(self, "No ship")

    def get_apparent_radius(self):
        return 0.0

class VisibleShip(ShipBase):
    anchor_class = 2
    editable = True
    orbit_rot_camera = False
    def __init__(self, name, ship_object, radius):
        ShipBase.__init__(self, name)
        self.ship_object = ship_object
        #TODO: Remove this
        self.ship_object.color_picking = False
        self.ship_object.shader.color_picking = False
        self.radius = radius
        self.add_component(ship_object)
        self.anchor.set_bounding_radius(radius)
        self.ship_object.set_scale(LVector3d(self.radius, self.radius, self.radius))
        return

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
        #TODO: Temporary workaround as some code need the shape to have an owner
        self.ship_object.set_owner(self)

        self.ship_object.set_scale(LVector3d(self.radius, self.radius, self.radius))

        self.shadow_caster = None
        self.create_own_shadow_caster = True

    def check_settings2(self):
        self.ship_object.check_settings()
        if self.shadow_caster is not None:
            self.shadow_caster.check_settings()

    def get_user_parameters2(self):
        parameters = self.ship_object.get_user_parameters()
        group = ParametersGroup(self.get_name(), parameters)
        return group

    def update_user_parameters2(self):
        self.ship_object.update_user_parameters()

    def get_apparent_radius(self):
        return self.radius

    def get_bounding_radius(self):
        return self.radius

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
        pos = self.get_local_position() + self.vector_to_star * self.get_bounding_radius()
        self.place_pos_only(self.light_source, pos, camera_pos, self.distance_to_obs, self.vector_to_obs)
        self.directional_light.setDirection(LVector3(*-self.vector_to_star))

    def remove_light(self):
        self.light_source.remove_node()
        self.light_source = None
        self.directional_light = None

    def update(self, time, dt):
        ShipBase.update(self, time, dt)
        self.ship_object.update(time, dt)

    def update_obs2(self, observer):
        self.rel_position = self._local_position - observer.get_local_position()
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

    def check_visibility2(self, frustum, pixel_size):
        self.ship_object.check_visibility(frustum, pixel_size)

    def update_shader(self):
        ShipBase.update_shader(self)
        self.ship_object.update_shader()

    def check_and_update_instance2(self, camera_pos, camera_rot):
        self.scene_rel_position = self.rel_position
        self.scene_position, self.scene_distance, self.scene_scale_factor = self.calc_scene_params(self.rel_position, self._position, self.distance_to_obs, self.vector_to_obs)
        self.scene_orientation = self._orientation
        self.ship_object.check_and_update_instance(camera_pos, camera_rot)
        self.instance = self.ship_object.instance
        self.instance.hide(self.AllCamerasMask)
        self.instance.show(self.NearCameraFlag)
        self.instance.show(self.WaterCameraFlag)
        self.instance.show(self.ShadowCameraFlag)
        self.update_light(camera_pos)
        if self.create_own_shadow_caster:
            if self.shadow_caster is None:
                self.shadow_caster = CustomShadowMapShadowCaster(self, None)
                self.shadow_caster.create()
            self.shadow_caster.update()
            self.ship_object.shadows.start_update()
            self.shadow_caster.add_target(self.ship_object)
            self.ship_object.shadows.end_update()

    def remove_instance2(self):
        self.ship_object.remove_instance()
        self.instance = None
        if self.shadow_caster is not None:
            self.shadow_caster.remove()
            self.shadow_caster = None
            self.remove_light()

class ActorShip(VisibleShip):
    pass
