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


from ..lights import LightSources
from .sceneworld import Worlds, ObserverCenteredWorld
from cosmonium.engine.anchors import ObserverAnchor


class FlatUniverse(Worlds):
    def __init__(self, terrain = None):
        Worlds.__init__(self)
        self.terrain = terrain
        if terrain is not None:
            self.add_world(terrain)
        self.lights = LightSources()
        self.scattering = None
        self.anchor = ObserverAnchor(0, self)

    @property
    def surface(self):
        return self.terrain

    def add_light(self, light):
        self.lights.add_light(light)

    def get_min_radius(self):
        return 6360 * 1000

    def get_average_radius(self):
        return 6360 * 1000

    def set_scattering(self, scattering):
        self.scattering = scattering
        if scattering is not None:
            scattering.set_light(self.lights.lights[0])
            scattering.set_inside(True)
            scattering.set_body(self)
        for world in self.worlds:
            world.set_scattering(self.scattering)

    def add_world(self, world):
        Worlds.add_world(self, world)
        world.set_lights(self.lights)
        if self.scattering is not None:
            world.set_scattering(self.scattering)

    def set_skybox(self, skybox):
        self.skybox = skybox
        world = ObserverCenteredWorld("skybox", background=True)
        world.add_component(skybox)
        self.add_world(world)

    def set_terrain(self, terrain):
        self.terrain = terrain
        self.add_world(terrain)

    def get_terrain(self):
        return self.terrain

    def update(self, time, dt, update_id, observer):
        Worlds.update(self, time, dt, update_id, observer)
        self.lights.update_lights()
        if self.scattering is not None:
            self.scattering.update(0, dt)
