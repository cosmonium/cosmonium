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

from ..bodies import EmissiveBody
from ..catalogs import objectsDB

from .yamlparser import YamlModuleParser
from .objectparser import ObjectYamlParser
from .orbitsparser import OrbitYamlParser
from .rotationsparser import RotationYamlParser
from .surfacesparser import SurfaceYamlParser

class NebulaYamlParser(YamlModuleParser):
    def decode(self, data):
        name = data.get('name')
        parent_name = data.get('parent')
        body_class = data.get('body-class', 'nebula')
        radius = data.get('radius')
        abs_magnitude = data.get('magnitude')
        orbit = OrbitYamlParser.decode(data.get('orbit'))
        rotation = RotationYamlParser.decode(data.get('rotation'))
        if data.get('surfaces') is None:
            surfaces = []
            surface = SurfaceYamlParser.decode_surface(data, None, {}, data)
        else:
            surfaces = SurfaceYamlParser.decode(data.get('surfaces'), None, data)
            surface = surfaces.pop(0)
        nebula = EmissiveBody(name,
                    body_class=body_class,
                    abs_magnitude=abs_magnitude,
                    radius=radius,
                    orbit=orbit,
                    rotation=rotation,
                    surface=surface)
        nebula.has_resolved_halo = False
        for surface in surfaces:
            nebula.add_surface(surface)
        if parent_name is not None:
            parent = objectsDB.get(parent_name)
            if parent is not None:
                parent.add_child_fast(nebula)
            else:
                print("ERROR: Parent '%s' of '%s' not found" % (parent_name, name))
            return None
        else:
            return nebula

ObjectYamlParser.register_object_parser('nebula', NebulaYamlParser())
