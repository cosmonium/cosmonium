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


from ..locallights import LocalDirectionalLight, LocalPointLight, LocalSpotLight
from .schemas.locallight import LocalDirectionalLightConfig, LocalPointLightConfig, LocalSpotLightConfig
from .yamlparser import TypedYamlParser, YamlModuleParser


class LocalDirectionalLightYamlParser(YamlModuleParser):

    @classmethod
    def decode(cls, data):
        # TODO: Disabled light is treated as non-existent, so we return None instead of a light object
        # Wwe should return a light object with a disabled flag instead of None
        if data.disabled:
            return None
        direction = data.direction.normalized()
        if data.shadows is not None:
            cast_shadows = True
            lens = data.shadows
        else:
            cast_shadows = False
            lens = None
        light = LocalDirectionalLight(
            data.name, data.position, data.color, data.power, direction, cast_shadows=cast_shadows, lens=lens
        )
        return light


class LocalPointLightYamlParser(YamlModuleParser):

    @classmethod
    def decode(cls, data):
        # TODO: Disabled light is treated as non-existent, so we return None instead of a light object
        # Wwe should return a light object with a disabled flag instead of None
        if data.disabled:
            return None
        light = LocalPointLight(
            data.name, data.position, data.color, data.power, data.attenuation, data.max_distance, cast_shadows=False
        )
        return light


class LocalSpotLightYamlParser(YamlModuleParser):

    @classmethod
    def decode(cls, data):
        # TODO: Disabled light is treated as non-existent, so we return None instead of a light object
        # Wwe should return a light object with a disabled flag instead of None
        if data.disabled:
            return None
        direction = data.direction.normalized()
        if data.shadows is not None:
            cast_shadows = True
            lens = data.shadows
        else:
            cast_shadows = False
            lens = None
        light = LocalSpotLight(
            data.name,
            data.position,
            data.color,
            data.power,
            data.attenuation,
            data.max_distance,
            (data.inner_cone, data.outer_cone),
            data.exponent,
            direction,
            cast_shadows=cast_shadows,
            lens=lens,
        )
        return light


class LocalLightYamlParser(TypedYamlParser):
    detect_trivial = False


LocalLightYamlParser.register_parser('directional', LocalDirectionalLightYamlParser, LocalDirectionalLightConfig)
LocalLightYamlParser.register_parser('point', LocalPointLightYamlParser, LocalPointLightConfig)
LocalLightYamlParser.register_parser('spot', LocalSpotLightYamlParser, LocalSpotLightConfig)
