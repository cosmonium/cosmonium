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


from .cartesianworldparser import CartesianWorldYamlParser
from .flatterrainworldparser import FlatTerrainWorldYamlParser
from .lightparser import InfiniteSunLightYamlParser
from .scatteringparser import ScatteringYamlParser
from .skyboxparser import SkyBoxYamlParser
from .yamlparser import YamlModuleParser


class FlatUniverseYamlParser(YamlModuleParser):
    def __init__(self, universe=None):
        YamlModuleParser.__init__(self)
        self.universe = universe

    def set_universe(self, universe):
        self.universe = universe

    def decode(self, data, parent=None):
        terrain = FlatTerrainWorldYamlParser.decode(data.get('terrain'))
        self.universe.set_terrain(terrain)
        #children = ObjectYamlParser.decode(data.get('children', []), self.universe)
        for light_data in data.get('lights', []):
            light = InfiniteSunLightYamlParser.decode(light_data)
            self.universe.add_light(light)
        scattering = ScatteringYamlParser.decode(data.get('scattering'))
        self.universe.set_scattering(scattering)
        skybox = SkyBoxYamlParser.decode({}, scattering)
        self.universe.set_skybox(skybox)
        for world_data in data.get('worlds', []):
            world = CartesianWorldYamlParser.decode(world_data, parent=self.universe)
            self.universe.add_world(world)
