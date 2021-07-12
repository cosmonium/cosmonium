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


from panda3d.core import LVector3
from panda3d.core import DirectionalLight

from .foundation import BaseObject
from .datasource import DataSource
from . import settings

class LightSource:
    def __init__(self, source, target):
        self.source = source
        self.target = target
        self.directional_light = None
        self.light_direction = self.target.anchor._local_position - self.source.anchor._local_position
        self.light_distance = self.light_direction.length()
        self.light_direction /= self.light_distance

    def create_light(self):
        self.directional_light = DirectionalLight('light_source')
        self.directional_light.setDirection(LVector3(*self.light_direction))
        self.directional_light.setColor((1, 1, 1, 1))
        self.light_source = BaseObject.context.world.attachNewNode(self.directional_light)

    def update_light(self, camera_pos):
        pos = self.target.get_local_position() - self.light_direction * self.target.get_extend()
        BaseObject.place_pos_only(self.light_source, pos, camera_pos, self.target.anchor.distance_to_obs, self.target.anchor.vector_to_obs)
        self.directional_light.setDirection(LVector3(*self.light_direction))

    def remove_light(self):
        self.light_source.remove_node()
        self.light_source = None
        self.directional_light = None

    def apply(self, instance):
        pass

    def update(self, instance):
        light_color = self.source.light_color
        instance.setShaderInput("light_dir", *-self.light_direction)
        instance.setShaderInput("light_color", light_color)
        instance.setShaderInput("ambient_coef", settings.corrected_global_ambient)
        instance.setShaderInput("ambient_color", (1, 1, 1, 1))

class LightSources(DataSource):
    def __init__(self):
        DataSource.__init__(self, 'lights')
        self.sources = []

    def add_source(self, source):
        self.sources.append(source)
        source.create_light()

    def remove_source(self, source):
        self.sources.remove(source)

    def remove_all(self):
        for source in self.sources:
            source.remove_light()
        self.sources = []

    def get_light_for(self, light_source):
        for source in self.sources:
            if source.source is light_source:
                return source
        return None

    def update_lights(self, camera_pos):
        for source in self.sources:
            source.update_light(camera_pos)

    def apply(self, shape, instance):
        for source in self.sources:
            source.apply(instance)

    def update(self, shape, instance):
        for source in self.sources:
            source.update(instance)
