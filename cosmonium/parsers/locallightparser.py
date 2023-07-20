#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2023 Laurent Deru.
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


from dataclasses import dataclass
from panda3d.core import LVector3, LPoint3, LColor
from typing import Optional

from ..locallights import LocalDirectionalLight, LocalPointLight, LocalSpotLight

from .yamlparser import YamlModuleParser


@dataclass
class ShadowsLens:
    near: float
    far: float
    width: Optional[float] = None
    height: Optional[float] = None


class LocalDirectionalLightYamlParser(YamlModuleParser):

    @classmethod
    def decode(self, data):
        if data is None: return None
        name = data.get('name')
        position = data.get('position', (0, 0, 0))
        position = LPoint3(*position)
        color = data.get('color', (1, 1, 1))
        if len(color) == 3:
            color = LColor(*color, 1)
        else:
            color = LColor(*color)
        power = data.get('power', 1)
        direction = data.get('direction', (0, 1, 0))
        direction = LVector3(*direction)
        direction.normalize()
        shadows_data = data.get("shadows")
        if shadows_data is not None:
            cast_shadows = True
            lens = ShadowsLens(shadows_data.get('near', 0), shadows_data.get('far', 100), shadows_data.get('width', 10), shadows_data.get('height', 10))
        else:
            cast_shadows = False
            lens = None
        light = LocalDirectionalLight(name, position, color, power, direction, cast_shadows=cast_shadows, lens=lens)
        return light


class LocalPointLightYamlParser(YamlModuleParser):

    @classmethod
    def decode(self, data):
        if data is None: return None
        name = data.get('name')
        position = data.get('position', (0, 0, 0))
        position = LPoint3(*position)
        color = data.get('color', (1, 1, 1))
        if len(color) == 3:
            color = LColor(*color, 1)
        else:
            color = LColor(*color)
        power = data.get('power', 1)
        attenuation = data.get('attenuation', (1, 0, 1))
        attenuation = LVector3(*attenuation)
        max_distance = data.get('max-distance', 1)
        shadows_data = data.get("shadows")
        cast_shadows = False
        light = LocalPointLight(name, position, color, power, attenuation, max_distance, cast_shadows=cast_shadows)
        return light


class LocalSpotLightYamlParser(YamlModuleParser):

    @classmethod
    def decode(self, data):
        if data is None: return None
        name = data.get('name')
        position = data.get('position', (0, 0, 0))
        position = LPoint3(*position)
        color = data.get('color', (1, 1, 1))
        if len(color) == 3:
            color = LColor(*color, 1)
        else:
            color = LColor(*color)
        power = data.get('power', 1)
        attenuation = data.get('attenuation', (1, 0, 1))
        attenuation = LVector3(*attenuation)
        max_distance = data.get('max-distance', 1)
        inner_cone_angle = data.get('inner-cone', 0)
        outer_cone_angle = data.get('outer-cone', 45)
        exponent = data.get('exponent')
        direction = data.get('direction', (0, 1, 0))
        direction = LVector3(*direction)
        direction.normalize()
        shadows_data = data.get("shadows")
        if shadows_data is not None:
            cast_shadows = True
            lens = ShadowsLens(shadows_data.get('near', 0), shadows_data.get('far', 100))
        else:
            cast_shadows = False
            lens = None
        light = LocalSpotLight(name, position, color, power, attenuation, max_distance, (inner_cone_angle, outer_cone_angle), exponent, direction, cast_shadows=cast_shadows, lens=lens)
        return light


class LocalLightYamlParser(YamlModuleParser):

    parsers = {}

    @classmethod
    def register(cls, name, parser):
        cls.parsers[name] = parser

    @classmethod
    def decode(cls, data):
        (object_type, parameters) = cls.get_type_and_data(data, detect_trivial=False)
        if object_type in cls.parsers:
            parser = cls.parsers[object_type]
            light = parser.decode(parameters)
        else:
            print("Unknown light type type '%s'" % object_type, data)
            light = None
        return light

LocalLightYamlParser.register('directional', LocalDirectionalLightYamlParser)
LocalLightYamlParser.register('point', LocalPointLightYamlParser)
LocalLightYamlParser.register('spot', LocalSpotLightYamlParser)
