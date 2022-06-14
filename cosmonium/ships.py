#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2021 Laurent Deru.
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


from panda3d.core import LPoint3d, LVector3d, LQuaterniond

from .scene.sceneworld import CartesianWorld
from .camera import CameraController
from .parameters import ParametersGroup

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

    def create_scene_anchor(self):
        anchor = ShipBase.create_scene_anchor(self)
        anchor.virtual_object = True
        return anchor

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
        ship_object.set_body(self)
        self.anchor.set_bounding_radius(radius)
        self.ship_object.set_scale(LVector3d(self.radius, self.radius, self.radius))

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

    def self_shadows_update(self, light_source):
        self.ship_object.add_self_shadow(light_source)


class ActorShip(VisibleShip):
    pass
