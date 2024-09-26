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

from ..objects.rings import StellarRings

from .elementsparser import RingsYamlParser
from .framesparser import FrameYamlParser
from .objectparser import ObjectYamlParser
from .orbitsparser import OrbitYamlParser
from .rotationsparser import RotationYamlParser
from .utilsparser import check_parent
from .yamlparser import YamlModuleParser


class StellarRingsYamlParser(YamlModuleParser):
    def __init__(self, body_class):
        self.body_class = body_class

    def decode(self, data, parent=None):
        name = data.get('name')
        (translated_names, source_names) = self.translate_names(name)
        parent_name = data.get('parent')
        parent, _explicit_parent = check_parent(name, parent, parent_name)
        if parent is None:
            return None
        actual_parent = parent.primary or parent
        body_class = data.get('body-class', self.body_class)
        rings_object = RingsYamlParser.decode(data)
        point_color = data.get('point-color', [1, 1, 1])
        point_color = LColor(point_color[0], point_color[1], point_color[2], 1.0)
        frame = FrameYamlParser.decode(data.get('frame'), actual_parent, default="mean-equatorial")
        orbit = OrbitYamlParser.decode(data.get('orbit'), frame, actual_parent)
        rotation = RotationYamlParser.decode(data.get('rotation'), frame, actual_parent, default="fixed")
        body = StellarRings(
            names=translated_names,
            source_names=source_names,
            body_class=body_class,
            rings_object=rings_object,
            orbit=orbit,
            rotation=rotation,
            frame=None,
            point_color=point_color,
        )
        parent.add_child_fast(body)
        return body


ObjectYamlParser.register_object_parser('rings', StellarRingsYamlParser('rings'))
