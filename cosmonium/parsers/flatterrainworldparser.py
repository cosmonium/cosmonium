# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
#
# Cosmonium is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Cosmonium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#


from ..scene.sceneworld import FlatTerrainWorld

from .populatorsparser import PopulatorYamlParser
from .surfacesparser import FlatSurfaceParser
from .yamlparser import YamlModuleParser


class FlatTerrainWorldYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        terrain_surface = FlatSurfaceParser.decode(data)
        flat_world = FlatTerrainWorld("terrain")
        flat_world.set_terrain(terrain_surface)
        layers = data.get('layers', [])
        for layer_data in layers:
            layer = PopulatorYamlParser.decode(layer_data)
            flat_world.add_component(layer)
            layer.set_terrain(terrain_surface)
            # TODO
            terrain_surface.shape.add_linked_object(layer)
        return flat_world
