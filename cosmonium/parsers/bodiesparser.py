#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2026 Laurent Deru.
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


from panda3d.core import LColor

from ..objects.reflective import ReflectiveBody
from .atmospheresparser import AtmosphereYamlParser
from .cloudsparser import CloudsYamlParser
from .controllersparser import ControllerYamlParser
from .framesparser import FrameYamlParser
from .objectparser import ObjectYamlParser
from .orbitsparser import OrbitYamlParser
from .rotationsparser import RotationYamlParser
from .schemas.stellarobjects import ReflectiveBodyConfig
from .surfacesparser import SurfaceYamlParser
from .utilsparser import check_parent, get_radius_scale
from .yamlparser import YamlModuleParser


class ReflectiveYamlParser(YamlModuleParser):
    def __init__(self, body_class):
        self.body_class = body_class

    def decode(self, data, parent=None):
        name = data.name
        translated_names, source_names = self.translate_names(name, reflective=True)
        parent_name = data.parent
        parent, explicit_parent = check_parent(name, parent, parent_name)
        if parent is None:
            return None
        actual_parent = parent.primary or parent
        body_class = data.body_class or self.body_class
        radius, ellipticity, scale = get_radius_scale(data, None)
        albedo = data.albedo
        atmosphere = AtmosphereYamlParser.decode(data.atmosphere)
        clouds = CloudsYamlParser.decode(data.clouds)
        point_color = data.point_color
        if point_color is None:
            point_color = LColor(1, 1, 1, 1)
        frame = FrameYamlParser.decode(data.frame, actual_parent)
        if data.controller is None:
            orbit = OrbitYamlParser.decode(data.orbit, frame, actual_parent)
            rotation = RotationYamlParser.decode(data.rotation, frame, actual_parent)
            frame = None
        else:
            orbit = None
            rotation = None
        body = ReflectiveBody(
            names=translated_names,
            source_names=source_names,
            body_class=body_class,
            radius=radius,
            oblateness=ellipticity,
            scale=scale,
            orbit=orbit,
            rotation=rotation,
            frame=frame,
            atmosphere=atmosphere,
            clouds=clouds,
            point_color=point_color,
            albedo=albedo,
        )
        if data.surfaces is None:
            surfaces = []
            surface_data = {
                'shape': data.shape,
                'appearance': data.appearance,
            }
            surfaces.append(SurfaceYamlParser.decode_surface(surface_data, {}, body))
        else:
            surfaces = SurfaceYamlParser.decode(data.surfaces, body)
        for surface in surfaces:
            body.add_surface(surface)
        parent.add_child_fast(body)
        controller_data = data.controller
        if controller_data is not None:
            controller = ControllerYamlParser.decode(controller_data, body.anchor)
            self.app.add_controller(controller)
        rings = data.rings
        if rings is not None:
            rings['name'] = data.name + "'s rings"
            rings['type'] = 'rings'
            if parent.primary is not body:
                system = body.get_or_create_system()
                body = system
            else:
                system = parent
            ObjectYamlParser.decode(rings, parent=system)
        return body


def register_body_parsers():
    ObjectYamlParser.register_object_parser('reflective', ReflectiveYamlParser(None), model=ReflectiveBodyConfig)
    ObjectYamlParser.register_object_parser('planet', ReflectiveYamlParser('planet'), model=ReflectiveBodyConfig)
    ObjectYamlParser.register_object_parser(
        'dwarfplanet', ReflectiveYamlParser('dwarfplanet'), model=ReflectiveBodyConfig
    )
    ObjectYamlParser.register_object_parser('moon', ReflectiveYamlParser('moon'), model=ReflectiveBodyConfig)
    ObjectYamlParser.register_object_parser('minormoon', ReflectiveYamlParser('minormoon'), model=ReflectiveBodyConfig)
    ObjectYamlParser.register_object_parser('lostmoon', ReflectiveYamlParser('lostmoon'), model=ReflectiveBodyConfig)
    ObjectYamlParser.register_object_parser('asteroid', ReflectiveYamlParser('asteroid'), model=ReflectiveBodyConfig)
    ObjectYamlParser.register_object_parser('comet', ReflectiveYamlParser('comet'), model=ReflectiveBodyConfig)
    ObjectYamlParser.register_object_parser(
        'interstellar', ReflectiveYamlParser('interstellar'), model=ReflectiveBodyConfig
    )
    ObjectYamlParser.register_object_parser(
        'spacecraft', ReflectiveYamlParser('spacecraft'), model=ReflectiveBodyConfig
    )
