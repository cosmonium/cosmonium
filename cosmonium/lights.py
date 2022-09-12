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


from math import pi

from panda3d.core import LVector3, LColor
from panda3d.core import DirectionalLight

from .astro.astro import abs_mag_to_lum
from .astro import units
from .datasource import DataSource
from . import settings

class SurrogateLight:
    def __init__(self, source, target):
        self.source = source
        self.target = target
        self.light_node = None
        self.light_instance = None
        self.light_direction = None
        self.light_distance = None

    def create_light(self):
        self.light_node = DirectionalLight('light_source')
        #self.light_node.set_direction(LVector3(*self.light_direction))
        self.light_node.set_color((1, 1, 1, 1))

    def create_light_node(self):
        self.light_instance = self.target.scene_anchor.unshifted_instance.attach_new_node(self.light_node)

    def update_light(self):
        self.light_direction = self.target.anchor.get_local_position() - self.source.anchor.get_local_position()
        self.light_distance = self.light_direction.length()
        self.light_direction /= self.light_distance

    def update_instance(self, camera_pos):
        if self.light_instance is None:
            self.create_light_node()
        pos = - self.light_direction * self.target.get_bounding_radius()
        self.light_instance.set_pos(*pos)
        self.light_node.set_direction(LVector3(*self.light_direction))

    def remove_light(self):
        self.light_instance.remove_node()
        self.light_instance = None
        self.light_node = None

    def apply(self, instance):
        pass

    def get_illuminance(self):
        light_color = LColor(self.source.light_color)
        luminosity = abs_mag_to_lum(self.source.get_abs_magnitude())
        illuminance = luminosity * units.sun_luminous_intensity / (self.light_distance * self.light_distance * 1000000)
        light_color *= illuminance
        return light_color

    def update(self, instance):
        light_color = LColor(self.source.light_color)
        if settings.use_pbr:
            luminosity = abs_mag_to_lum(self.source.get_abs_magnitude())
            illuminance = luminosity * units.sun_luminous_intensity / (self.light_distance * self.light_distance * 1000000)
            light_color *= illuminance
        instance.setShaderInput("light_dir", *-self.light_direction)
        instance.setShaderInput("light_color", light_color)
        instance.setShaderInput("ambient_coef", settings.corrected_global_ambient)
        instance.setShaderInput("ambient_color", (1, 1, 1, 1))

class LightSources(DataSource):
    def __init__(self):
        DataSource.__init__(self, 'lights')
        self.lights = []

    def add_light(self, light):
        self.lights.append(light)
        light.create_light()

    def remove_light(self, light):
        self.lights.remove(light)

    def remove_all(self):
        for source in self.lights:
            source.remove_light()
        self.lights = []

    def get_light_for(self, light_source):
        for light in self.lights:
            if light.source is light_source:
                return light
        return None

    def update_lights(self):
        for light in self.lights:
            light.update_light()

    def update_instances(self, camera_pos):
        for light in self.lights:
            light.update_instance(camera_pos)

    def apply(self, shape, instance):
        for light in self.lights:
            light.apply(instance)

    def update(self, shape, instance, camera_pos, camera_rot):
        for light in self.lights:
            light.update(instance)
