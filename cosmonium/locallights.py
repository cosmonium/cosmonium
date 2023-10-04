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


from math import pi, radians
from panda3d.core import DirectionalLight, PointLight, Spotlight
from panda3d.core import LColor, LQuaternion, LVector3, look_at

from .foundation import VisibleObject


class LocalLight(VisibleObject):

    concrete_object = False

    def __init__(self, name, position, color, power, attenuation, max_distance, cast_shadows):
        super().__init__(name)
        self.position = position
        self.color = color
        self.power = power
        self.attenuation = attenuation
        self.max_distance = max_distance
        self.cast_shadows = cast_shadows
        self.light_node = None
        self._node_color = LColor(self.color.xyz * self.power, 1)
        self.body = None

    def set_body(self, body):
        self.body = body

    def remove_instance(self):
        if self.instance is not None:
            self.light_node = None
            base.render.clear_light(self.instance)
        super().remove_instance()


class LocalDirectionalLight(LocalLight):
    def __init__(self, name, position, color, power, direction, cast_shadows, lens=None):
        super().__init__(name, position, color, power, None, None, cast_shadows)
        self.light_direction = direction
        self.lens = lens

    def create_instance(self):
        self.light_node = DirectionalLight(self.name)
        self.light_node.set_direction(self.light_direction)
        self.light_node.set_color(self._node_color)
        self.instance = self.scene_anchor.unshifted_instance.attach_new_node(self.light_node)
        self.instance.set_pos(self.position)
        #self.scene_anchor.unshifted_instance.set_light(self.instance)
        base.render.set_light(self.instance)
        if self.cast_shadows:
            self.light_node.set_shadow_caster(True, 1024, 1024)
            lens = self.light_node.get_lens()
            lens.set_near_far(self.lens.near, self.lens.far)
            lens.set_film_size(self.lens.width, self.lens.height)
            lens.set_view_vector(self.light_direction, LVector3.up())


class LocalPointLight(LocalLight):

    def create_instance(self):
        self.light_node = PointLight(self.name)
        self.light_node.set_color(self._node_color)
        if self.attenuation is not None:
            self.light_node.set_attenuation(self.attenuation)
        if self.max_distance is not None:
            self.light_node.set_max_distance(self.max_distance)
        self.instance = self.scene_anchor.unshifted_instance.attach_new_node(self.light_node)
        self.instance.set_pos(self.position)
        #self.scene_anchor.unshifted_instance.set_light(self.instance)
        base.render.set_light(self.instance)
        if self.cast_shadows:
            self.light_node.set_shadow_caster(True, 1024, 1024)

class LocalSpotLight(LocalLight):
    def __init__(self, name, position, color, power, attenuation, max_distance, cone, exponent, direction, cast_shadows, lens=None):
        super().__init__(name, position, color, power, attenuation, max_distance, cast_shadows)
        self.cone = cone
        self.exponent = exponent
        self.light_direction = direction
        self.lens = lens
        if self.exponent is None:
            exp = 8 / 3
            self.exponent = 2 * (pi * 0.5 / radians(cone[1])) ** exp

    def create_instance(self):
        self.light_node = Spotlight(self.name)
        self.light_node.set_color(self._node_color)
        if self.attenuation is not None:
            self.light_node.set_attenuation(self.attenuation)
        if self.max_distance is not None:
            self.light_node.set_max_distance(self.max_distance)
        self.light_node.set_exponent(self.exponent)
        self.instance = self.scene_anchor.unshifted_instance.attach_new_node(self.light_node)
        self.instance.set_pos(self.position)
        quat = LQuaternion()
        look_at(quat, self.light_direction)
        self.instance.set_quat(quat)
        lens = self.light_node.get_lens()
        lens.set_fov(self.cone[1] * 2, self.cone[1] * 2)
        #self.scene_anchor.unshifted_instance.set_light(self.instance)
        base.render.set_light(self.instance)
        if self.cast_shadows:
            self.light_node.set_shadow_caster(True, 1024, 1024)
            # lens.set_near_far(self.lens.near, self.lens.far)
