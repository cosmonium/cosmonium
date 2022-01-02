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


from panda3d.core import LColor

from ..bodies import ReflectiveBody

from .yamlparser import YamlModuleParser
from .objectparser import ObjectYamlParser
from .orbitsparser import OrbitYamlParser
from .rotationsparser import RotationYamlParser
from .atmospheresparser import AtmosphereYamlParser
from .elementsparser import CloudsYamlParser
from .surfacesparser import SurfaceYamlParser
from .ringsparser import StellarRingsYamlParser
from .framesparser import FrameYamlParser
from .controllersparser import ControllerYamlParser
from .utilsparser import check_parent, get_radius_scale

class ReflectiveYamlParser(YamlModuleParser):
    def __init__(self, body_class):
        self.body_class = body_class

    def decode(self, data, parent=None):
        name = data.get('name')
        (translated_names, source_names) = self.translate_names(name)
        parent_name = data.get('parent')
        parent, explicit_parent = check_parent(name, parent, parent_name)
        if parent is None: return None
        actual_parent = parent.primary or parent
        body_class = data.get('body-class', self.body_class)
        radius, ellipticity, scale = get_radius_scale(data, None)
        albedo = data.get('albedo', 0.5)
        atmosphere = AtmosphereYamlParser.decode(data.get('atmosphere'))
        clouds = CloudsYamlParser.decode(data.get('clouds'))
        point_color = data.get('point-color', [1, 1, 1])
        point_color = LColor(point_color[0], point_color[1], point_color[2], 1.0)
        frame = FrameYamlParser.decode(data.get('frame'), actual_parent)
        orbit = OrbitYamlParser.decode(data.get('orbit'), frame, actual_parent)
        rotation = RotationYamlParser.decode(data.get('rotation'), frame, actual_parent)
        body = ReflectiveBody(names=translated_names,
                              source_names=source_names,
                              body_class=body_class,
                              radius=radius,
                              oblateness=ellipticity,
                              scale=scale,
                              orbit=orbit,
                              rotation=rotation,
                              atmosphere=atmosphere,
                              clouds=clouds,
                              point_color=point_color,
                              albedo=albedo)
        if data.get('surfaces') is None:
            surfaces = []
            surfaces.append(SurfaceYamlParser.decode_surface(data, {}, body))
        else:
            surfaces = SurfaceYamlParser.decode(data.get('surfaces'), body)
        for surface in surfaces:
            body.add_surface(surface)
        parent.add_child_fast(body)
        controller_data = data.get('controller')
        if controller_data is not None:
            controller_class = ControllerYamlParser.decode(controller_data)
            controller = controller_class(body)
            self.app.add_controller(controller)
        rings = data.get('rings')
        if rings is not None:
            rings['name'] = data['name'] + "'s rings"
            rings_parser = StellarRingsYamlParser('rings')
            if parent.primary is not body:
                system = body.get_or_create_system()
                body = system
            else:
                system = parent
            rings_parser.decode(rings, system)
        return body

ObjectYamlParser.register_object_parser('reflective', ReflectiveYamlParser(None))
ObjectYamlParser.register_object_parser('planet', ReflectiveYamlParser('planet'))
ObjectYamlParser.register_object_parser('dwarfplanet', ReflectiveYamlParser('dwarfplanet'))
ObjectYamlParser.register_object_parser('moon', ReflectiveYamlParser('moon'))
ObjectYamlParser.register_object_parser('minormoon', ReflectiveYamlParser('minormoon'))
ObjectYamlParser.register_object_parser('lostmoon', ReflectiveYamlParser('lostmoon'))
ObjectYamlParser.register_object_parser('asteroid', ReflectiveYamlParser('asteroid'))
ObjectYamlParser.register_object_parser('comet', ReflectiveYamlParser('comet'))
ObjectYamlParser.register_object_parser('interstellar', ReflectiveYamlParser('interstellar'))
ObjectYamlParser.register_object_parser('spacecraft', ReflectiveYamlParser('spacecraft'))
