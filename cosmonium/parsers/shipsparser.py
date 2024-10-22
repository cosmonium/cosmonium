#
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


from panda3d.core import LPoint3d, LQuaterniond, LVector3d

from ..astro import units
from ..camera import CameraController
from ..components.elements.surfaces import MeshSurface
from ..shaders.rendering import RenderingShader
from ..shapes.mesh import MeshShape
from ..ships import VisibleShip

from .appearancesparser import AppearanceYamlParser
from .objectparser import ObjectYamlParser
from .shadersparser import LightingModelYamlParser
from .shapesparser import ShapeYamlParser
from .yamlparser import YamlModuleParser


class BaseShipYamlParser(YamlModuleParser):
    camera_modes = []

    @classmethod
    def decode(self, data):
        name = data.get('name')
        radius = data.get('radius', 10)
        radius_units = data.get('radius-units', units.m)
        radius *= radius_units
        camera_distance = data.get('camera-distance', None)
        camera_pos = data.get('camera-position', None)
        camera_pos_units = data.get('camera-position-units', units.m)
        camera_rot_data = data.get('camera-rotation', None)
        if camera_rot_data is not None:
            if len(camera_rot_data) == 3:
                camera_rot = LQuaterniond()
                camera_rot.set_hpr(LVector3d(*camera_rot_data))
            else:
                camera_rot = LQuaterniond(*camera_rot_data)
        else:
            camera_rot = LQuaterniond()
        shape = data.get('shape')
        appearance = data.get('appearance')
        lighting_model = data.get('lighting-model')
        shape, extra = ShapeYamlParser.decode(shape)
        if appearance is None:
            if isinstance(shape, MeshShape):
                appearance = 'model'
            else:
                appearance = 'textures'
        appearance = AppearanceYamlParser.decode(appearance)
        lighting_model = LightingModelYamlParser.decode(lighting_model, appearance)
        shader = RenderingShader(lighting_model=lighting_model, use_model_texcoord=not extra.get('create-uv', False))
        ship_object = MeshSurface('ship', shape=shape, appearance=appearance, shader=shader)
        if camera_distance is None:
            if camera_pos is None:
                camera_distance = 5.0
                camera_pos = LPoint3d(0, -camera_distance * radius, 0)
            else:
                camera_pos = LPoint3d(*camera_pos) * camera_pos_units
                camera_distance = camera_pos.length() / radius
        else:
            camera_pos = LPoint3d(0, -camera_distance * radius, 0)
        ship = VisibleShip(name, ship_object, radius)
        ship.set_camera_hints(camera_distance, camera_pos, camera_rot)
        for mode in self.camera_modes:
            ship.add_camera_mode(mode)
        self.app.add_ship(ship)


class CockpitYamlParser(BaseShipYamlParser):
    camera_modes = [CameraController.LOOK_AROUND]


class ShipYamlParser(BaseShipYamlParser):
    camera_modes = [CameraController.FOLLOW]


def register_ship_parsers():
    ObjectYamlParser.register_object_parser('cockpit', CockpitYamlParser())
    ObjectYamlParser.register_object_parser('ship', ShipYamlParser())
