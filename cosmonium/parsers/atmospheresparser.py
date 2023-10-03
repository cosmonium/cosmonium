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


from panda3d.core import LVector3d

from ..appearances import Appearance
from ..components.elements.atmosphere import Atmosphere
from ..scattering.oneil.oneil import ONeilSimpleScattering
from ..scattering.oneil.oneil import ONeilScattering
from ..shaders.rendering import RenderingShader
from ..shaders.lighting.base import AtmosphereLightingModel
from ..celestia.scattering import CelestiaScattering

from .yamlparser import YamlModuleParser
from .scatteringparser import ScatteringYamlParser
from .shapesparser import ShapeYamlParser


class CelestiaAtmosphereYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        atmosphere_height = data.get('height', None)
        mie_coef = data.get('mie', 0.0)
        mie_scale_height = data.get('mie-scale-height', 0.0)
        mie_phase_asymmetry = data.get('mie-asymmetry', 0.0)
        rayleigh_coef = data.get('rayleigh', None)
        rayleigh_scale_height = data.get('rayleigh-scale-height', 0.0)
        absorption_coef = data.get('absorption', None)
        appearance = Appearance()
        shape, extra = ShapeYamlParser.decode(data.get('shape', {'icosphere': {'subdivisions': 5}}))
        shader = RenderingShader(lighting_model=AtmosphereLightingModel())
        scattering = CelestiaScattering(
            height = atmosphere_height,
            shape=shape,
            appearance=appearance,
            mie_scale_height = mie_scale_height,
            mie_coef = mie_coef,
            mie_phase_asymmetry = mie_phase_asymmetry,
            rayleigh_coef = rayleigh_coef,
            rayleigh_scale_height = rayleigh_scale_height,
            absorption_coef = absorption_coef)
        atmosphere = Atmosphere(scattering, shape, appearance, shader)
        return atmosphere

class ONeilSimpleAtmosphereYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        scattering = ScatteringYamlParser.decode(data)
        appearance = Appearance()
        shape, extra = ShapeYamlParser.decode(data.get('shape', {'icosphere': {'subdivisions': 5}}))
        shader = RenderingShader(lighting_model=AtmosphereLightingModel())
        atmosphere = Atmosphere(scattering, shape, appearance, shader)
        return atmosphere

class ONeilAtmosphereYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        scattering = ScatteringYamlParser.decode(data)
        appearance = Appearance()
        shape, extra = ShapeYamlParser.decode(data.get('shape', {'icosphere': {'subdivisions': 5}}))
        shader = RenderingShader(lighting_model=AtmosphereLightingModel())
        atmosphere = Atmosphere(scattering, shape, appearance, shader)
        return atmosphere

class AtmosphereYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        if data is None: return None
        (object_type, parameters) = cls.get_type_and_data(data)
        if object_type == 'oneil:simple':
            return ONeilSimpleAtmosphereYamlParser.decode(parameters)
        elif object_type == 'oneil':
            return ONeilAtmosphereYamlParser.decode(parameters)
        elif object_type == 'celestia':
            return CelestiaAtmosphereYamlParser.decode(parameters)
        else:
            print("Atmosphpere type", object_type, "unknown")
            return None

