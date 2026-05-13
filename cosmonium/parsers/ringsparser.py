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


from panda3d.core import LColor

from ..components.elements.rings import Rings
from ..objects.rings import StellarRings
from ..shaders.rendering import RenderingShader
from .appearancesparser import AppearanceYamlParser
from .framesparser import FrameYamlParser
from .objectparser import ObjectYamlParser
from .orbitsparser import OrbitYamlParser
from .rotationsparser import RotationYamlParser
from .schemas.stellarobjects import StellarRingsConfig
from .shadersparser import LightingModelYamlParser
from .utilsparser import check_parent
from .yamlparser import YamlModuleParser


class StellarRingsYamlParser(YamlModuleParser):
    def __init__(self, body_class):
        self.body_class = body_class

    def decode(self, data, parent=None):
        name = data.name
        parent_name = data.parent
        parent, _explicit_parent = check_parent(name, parent, parent_name)
        if parent is None:
            return None
        actual_parent = parent.primary or parent
        body_class = data.body_class or self.body_class
        point_color = data.point_color
        if point_color is None:
            point_color = LColor(1, 1, 1, 1)
        frame = FrameYamlParser.decode(data.frame, actual_parent, default="mean-equatorial")
        orbit = OrbitYamlParser.decode(data.orbit, frame, actual_parent)
        rotation = RotationYamlParser.decode(data.rotation, frame, actual_parent, default="fixed")
        appearance = AppearanceYamlParser.decode(data.appearance, patched_shape=False)
        lighting_model = LightingModelYamlParser.decode(data.lighting_model, appearance)
        shader = RenderingShader(lighting_model=lighting_model)
        rings_object = Rings(data.inner_radius.scaled_value, data.outer_radius.scaled_value, appearance, shader)
        body = StellarRings(
            names=name,
            body_class=body_class,
            rings_object=rings_object,
            orbit=orbit,
            rotation=rotation,
            frame=None,
            point_color=point_color,
        )
        self.translate_object_names(body, body.anchor.get_names())
        parent.add_child_fast(body)
        return body


def register_rings_parsers():
    ObjectYamlParser.register_object_parser('rings', StellarRingsYamlParser('rings'), model=StellarRingsConfig)
