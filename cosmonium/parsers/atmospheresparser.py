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


from ..appearances import Appearance
from ..celestia.scattering import CelestiaScattering
from ..components.elements.atmosphere import Atmosphere
from ..shaders.lighting.base import AtmosphereLightingModel
from ..shaders.rendering import RenderingShader
from .scatteringparser import ScatteringYamlParser
from .schemas.atmosphere import CelestiaAtmosphereConfig, ONeilAtmosphereConfig, ONeilSimpleAtmosphereConfig
from .shapesparser import ShapeYamlParser
from .yamlparser import TypedYamlParser, YamlModuleParser


class CelestiaAtmosphereYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        appearance = Appearance()
        shape, extra = ShapeYamlParser.decode(data.shape, use_skirt=False)
        shader = RenderingShader(lighting_model=AtmosphereLightingModel())
        scattering = CelestiaScattering(
            height=data.height,
            appearance=appearance,
            mie_scale_height=data.mie_scale_height,
            mie_coef=data.mie,
            mie_phase_asymmetry=data.mie_asymmetry,
            rayleigh_coef=data.rayleigh,
            rayleigh_scale_height=data.rayleigh_scale_height,
            absorption_coef=data.absorption,
        )
        atmosphere = Atmosphere(scattering, shape, appearance, shader)
        return atmosphere


class ONeilSimpleAtmosphereYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        scattering = ScatteringYamlParser.decode(data)
        appearance = Appearance()
        if data.shape is None:
            shape = {'icosphere': {'subdivisions': 5}}
        else:
            shape = data.shape
        shape, extra = ShapeYamlParser.decode(shape, use_skirt=False)
        shader = RenderingShader(lighting_model=AtmosphereLightingModel())
        atmosphere = Atmosphere(scattering, shape, appearance, shader)
        return atmosphere


class ONeilAtmosphereYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        scattering = ScatteringYamlParser.decode(data)
        appearance = Appearance()
        if data.shape is None:
            shape = {'icosphere': {'subdivisions': 5}}
        else:
            shape = data.shape
        shape, extra = ShapeYamlParser.decode(shape, use_skirt=False)
        shader = RenderingShader(lighting_model=AtmosphereLightingModel())
        atmosphere = Atmosphere(scattering, shape, appearance, shader)
        return atmosphere


class AtmosphereYamlParser(TypedYamlParser):
    @classmethod
    def decode(cls, data):
        if data is None:
            return None
        (object_type, parameters) = cls.get_type_and_data(data)
        validated_data = cls.validate_and_decode(object_type, parameters)
        if object_type == 'oneil:simple':
            return ONeilSimpleAtmosphereYamlParser.decode(validated_data)
        elif object_type == 'oneil':
            return ONeilAtmosphereYamlParser.decode(validated_data)
        elif object_type == 'celestia':
            return CelestiaAtmosphereYamlParser.decode(validated_data)
        else:
            print("Atmosphpere type", object_type, "unknown")
            return None


def register_atmosphere_parsers():
    """Register atmosphere parsers with their corresponding Pydantic models."""
    AtmosphereYamlParser.register_parser('celestia', CelestiaAtmosphereYamlParser, CelestiaAtmosphereConfig)
    AtmosphereYamlParser.register_parser('oneil:simple', ONeilSimpleAtmosphereYamlParser, ONeilSimpleAtmosphereConfig)
    AtmosphereYamlParser.register_parser('oneil', ONeilAtmosphereYamlParser, ONeilAtmosphereConfig)
