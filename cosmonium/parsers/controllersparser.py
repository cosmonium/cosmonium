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


from panda3d.core import LPoint3d

from ..catalogs import objectsDB
from ..controllers.position import FlatSurfaceMovementController, SurfaceMovementController
from ..plugins import moduleLoader
from .objectparser import ObjectYamlParser
from .utilsparser import AngleUnitsYamlParser, DistanceUnitsYamlParser
from .yamlparser import TypedYamlParser, YamlModuleParser


class ScriptControllerYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, anchor):
        filename = data.get('file')
        module_path = cls.context.find_module(filename)
        module = moduleLoader.load_module(module_path)
        controller = module.ControllerClass(anchor)
        return controller


class SurfaceControllerYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, anchor):
        long = data.get('long', 0.0)
        long_units = AngleUnitsYamlParser.decode(data.get('long-units', 'Deg'))
        lat = data.get('lat', 0.0)
        lat_units = AngleUnitsYamlParser.decode(data.get('lat-units', 'Deg'))
        altitude = data.get('altitude', 0)
        altitude_units = DistanceUnitsYamlParser.decode(data.get('altitude-units', 'm'))
        return SurfaceMovementController(
            anchor, anchor.parent.body.primary, long * long_units, lat * lat_units, altitude * altitude_units
        )


class FlatSurfaceControllerYamlParser(YamlModuleParser):

    @classmethod
    def decode(cls, data, anchor):
        position = data.get('position', [0, 0, 0])
        altitude = data.get('altitude', 0)
        if len(position) == 3:
            position = LPoint3d(*position)
        else:
            position = LPoint3d(*position, 0)
        # Terrain is not known at this stage.
        return FlatSurfaceMovementController(anchor, None, position, altitude)


class ControllerYamlParser(TypedYamlParser):

    @classmethod
    def decode(cls, data, anchor):
        (object_type, parameters) = cls.get_type_and_data(data, detect_trivial=False)
        if object_type in cls.parsers:
            parser = cls.parsers[object_type]
            controller = parser.decode(parameters, anchor)
        else:
            print("Unknown controller type '%s'" % object_type, data)
            controller = None
        return controller


ControllerYamlParser.register_parser('script', ScriptControllerYamlParser())
ControllerYamlParser.register_parser('surface', SurfaceControllerYamlParser())
ControllerYamlParser.register_parser('flat-surface', FlatSurfaceControllerYamlParser())


class StandaloneControllerYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        name = data.get('name', None)
        body_name = data.get('body')
        body = objectsDB.get(body_name)
        if body is None:
            print("ERROR: Parent '%s' of controller '%s' not found" % (body_name, name))
            return None
        controller_class = ControllerYamlParser.decode(data)
        controller = controller_class(body)
        cls.app.add_controller(controller)
        return None


ObjectYamlParser.register_object_parser('controller', StandaloneControllerYamlParser())
