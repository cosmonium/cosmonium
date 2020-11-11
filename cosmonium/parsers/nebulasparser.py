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
from .utilsparser import check_parent

class NebulaYamlParser(YamlModuleParser):
    def decode(self, data, parent=None):
        name = data.get('name')
        (translated_names, source_names) = self.translate_names(name)
        parent_name = data.get('parent')
        parent, explicit_parent = check_parent(name, parent, parent_name)
        if parent is None: return None
        body_class = data.get('body-class', 'nebula')
        radius = data.get('radius')
        abs_magnitude = data.get('magnitude')
        orbit = OrbitYamlParser.decode(data.get('orbit'), None, parent)
        rotation = RotationYamlParser.decode(data.get('rotation'), None, parent)
        if data.get('surfaces') is None:
            surfaces = []
            surface = SurfaceYamlParser.decode_surface(data, None, {}, data)
        else:
            surfaces = SurfaceYamlParser.decode(data.get('surfaces'), None, data)
            surface = surfaces.pop(0)
        nebula = EmissiveBody(translated_names,
                    source_names,
                    body_class=body_class,
                    abs_magnitude=abs_magnitude,
                    radius=radius,
                    orbit=orbit,
                    rotation=rotation,
                    surface=surface)
        nebula.has_resolved_halo = False
        for surface in surfaces:
            nebula.add_surface(surface)
        if explicit_parent:
            parent.add_child_fast(nebula)
        if parent_name is not None:
            return None
        else:
            return nebula

ObjectYamlParser.register_object_parser('nebula', NebulaYamlParser())
