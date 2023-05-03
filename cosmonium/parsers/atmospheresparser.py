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
from ..scattering.oneil.oneil import ONeilSimpleAtmosphere
from ..scattering.oneil.oneil import ONeilAtmosphere
from ..celestia.atmosphere import CelestiaAtmosphere

from .yamlparser import YamlModuleParser
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
        atmosphere = CelestiaAtmosphere(height = atmosphere_height,
                                    shape=shape,
                                    appearance=appearance,
                                    mie_scale_height = mie_scale_height,
                                    mie_coef = mie_coef,
                                    mie_phase_asymmetry = mie_phase_asymmetry,
                                    rayleigh_coef = rayleigh_coef,
                                    rayleigh_scale_height = rayleigh_scale_height,
                                    absorption_coef = absorption_coef)
        return atmosphere

class ONeilSimpleAtmosphereYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        mie_phase_asymmetry = data.get('g', -0.99)
        rayleigh_coef = data.get('rayleigh', 0.0025)
        mie_coef = data.get('mie', 0.0015)
        sun_power = data.get('power', 15.0)
        samples = data.get('samples', 5)
        exposure = data.get('exposure', 0.8)
        calc_in_fragment = data.get('calc-in-fragment', True)
        normalize = data.get('normalize', True)
        hdr = data.get('hdr', True)
        atm_calc_in_fragment = data.get('atm-calc-in-fragment', True)
        atm_normalize = data.get('atm-normalize', True)
        atm_hdr = data.get('atm-hdr', True)
        appearance = Appearance()
        shape, extra = ShapeYamlParser.decode(data.get('shape', {'icosphere': {'subdivisions': 5}}))
        atmosphere = ONeilSimpleAtmosphere(shape=shape,
                                           wavelength = [0.650, 0.570, 0.465],
                                           mie_phase_asymmetry=mie_phase_asymmetry,
                                           mie_coef=mie_coef,
                                           rayleigh_coef=rayleigh_coef,
                                           sun_power=sun_power,
                                           samples=samples,
                                           exposure=exposure,
                                           calc_in_fragment=calc_in_fragment,
                                           atm_calc_in_fragment=atm_calc_in_fragment,
                                           normalize=normalize,
                                           atm_normalize=atm_normalize,
                                           hdr=hdr,
                                           atm_hdr=atm_hdr,
                                           appearance=appearance)
        return atmosphere

class ONeilAtmosphereYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        height = data.get('height', 160)
        mie_phase_asymmetry = data.get('g', -0.85)
        rayleigh_scale_depth = data.get('rayleigh-scale-depth', 0.25 * height)
        rayleigh_coef = data.get('rayleigh', 0.0025)
        rayleigh_absorption = LVector3d(*(data.get('rayleigh-absorption', [0, 0, 0])))
        mie_scale_depth = data.get('mie-scale-depth', 0.1 * height)
        mie_alpha_coef = data.get('mie-alpha', 0)
        mie_beta_coef = data.get('mie', 0.0015)
        sun_power = data.get('power', 15.0)
        samples = data.get('samples', 32)
        calc_in_fragment = data.get('calc-in-fragment', True)
        normalize = data.get('normalize', True)
        hdr = data.get('hdr', True)
        exposure = data.get('exposure', 1)
        atm_calc_in_fragment = data.get('atm-calc-in-fragment', True)
        atm_normalize = data.get('atm-normalize', True)
        atm_hdr = data.get('atm-hdr', True)
        atm_exposure = data.get('atm-exposure', 0.8)
        rayleigh_scale_depth /= height
        mie_scale_depth /= height
        appearance = Appearance()
        shape, extra = ShapeYamlParser.decode(data.get('shape', {'icosphere': {'subdivisions': 5}}))
        atmosphere = ONeilAtmosphere(shape=shape,
                                     height=height,
                                     wavelength = [0.650, 0.570, 0.465],
                                     mie_phase_asymmetry=mie_phase_asymmetry,
                                     rayleigh_scale_depth=rayleigh_scale_depth,
                                     rayleigh_coef=rayleigh_coef,
                                     rayleigh_absorption=rayleigh_absorption,
                                     mie_scale_depth=mie_scale_depth,
                                     mie_alpha_coef=mie_alpha_coef,
                                     mie_beta_coef=mie_beta_coef,
                                     sun_power=sun_power,
                                     samples=samples,
                                     calc_in_fragment=calc_in_fragment,
                                     atm_calc_in_fragment=atm_calc_in_fragment,
                                     normalize=normalize,
                                     atm_normalize=atm_normalize,
                                     hdr=hdr,
                                     exposure=exposure,
                                     atm_hdr=atm_hdr,
                                     atm_exposure=atm_exposure,
                                     lookup_size=256,
                                     lookup_samples=50,
                                     appearance=appearance)
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

