#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2019 Laurent Deru.
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

from ..bodies import Star
from ..catalogs import objectsDB
from ..procedural.stars import proceduralStarSurfaceFactoryDB
from ..procedural.stars import ProceduralStarSurfaceFactory

from .yamlparser import YamlModuleParser
from .objectparser import ObjectYamlParser
from .orbitsparser import OrbitYamlParser
from .rotationsparser import RotationYamlParser
from .noiseparser import NoiseYamlParser

class StarYamlParser(YamlModuleParser):
    def decode(self, data):
        name = data.get('name')
        parent_name = data.get('parent')
        body_class = data.get('body-class', 'star')
        radius = data.get('radius')
        temperature = data.get('temperature')
        abs_magnitude = data.get('magnitude')
        spectral_type = data.get('spectral-type')
        orbit = OrbitYamlParser.decode(data.get('orbit'))
        rotation = RotationYamlParser.decode(data.get('rotation'))
        factory = proceduralStarSurfaceFactoryDB.get('default')
        star = Star(name,
                    body_class=body_class,
                    surface_factory=factory,
                    abs_magnitude=abs_magnitude,
                    temperature=temperature,
                    spectral_type=spectral_type,
                    radius=radius,
                    orbit=orbit,
                    rotation=rotation)
        if parent_name is not None:
            parent = objectsDB.get(parent_name)
            if parent is not None:
                parent.add_child_fast(star)
            else:
                print("ERROR: Parent '%s' of '%s' not found" % (parent_name, name))
            return None
        else:
            return star
    
class StarSurfaceFactoryYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        name = data.get('name')
        noise_parser = NoiseYamlParser()
        noise = noise_parser.decode(data.get('noise'))
        size = int(data.get('size', 256))
        factory = ProceduralStarSurfaceFactory(noise, size)
        proceduralStarSurfaceFactoryDB.add(name, factory)
        return None

ObjectYamlParser.register_object_parser('star', StarYamlParser())
ObjectYamlParser.register_object_parser('star-surface', StarSurfaceFactoryYamlParser())
