from __future__ import print_function
from __future__ import absolute_import

from ..bodyelements import NoAtmosphere
from ..shaders import BasicShader, LightingModel
from ..appearances import Appearance
from ..oneil import ONeilScattering, ONeilAtmosphere
from ..celestia.atmosphere import CelestiaScattering, CelestiaAtmosphere

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
        lighting_model = CelestiaScattering(atmosphere=True)
        shader = BasicShader(lighting_model=lighting_model)
        shape, extra = ShapeYamlParser.decode(data.get('shape', {'icosphere': {'subdivisions': 5}}))
        atmosphere = CelestiaAtmosphere(height = atmosphere_height,
                                    shape=shape,
                                    appearance=appearance,
                                    shader=shader,
                                    mie_scale_height = mie_scale_height,
                                    mie_coef = mie_coef,
                                    mie_phase_asymmetry = mie_phase_asymmetry,
                                    rayleigh_coef = rayleigh_coef,
                                    rayleigh_scale_height = rayleigh_scale_height,
                                    absorption_coef = absorption_coef)
        return atmosphere

class ONeilAtmosphereYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        mie_phase_asymmetry = data.get('g', -0.99)
        rayleigh_coef = data.get('rayleigh', 0.0025)
        mie_coef = data.get('mie', 0.0015)
        sun_power = data.get('power', 15.0)
        wavelength = data.get('wavelength', [0.650, 0.570, 0.465])
        exposure = data.get('exposure', 0.8)
        calc_in_fragment = data.get('calc-in-fragment', False)
        normalize = data.get('normalize', False)
        hdr = data.get('hdr', False)
        atm_calc_in_fragment = data.get('atm-calc-in-fragment', True)
        atm_normalize = data.get('atm-normalize', True)
        atm_hdr = data.get('atm-hdr', True)
        appearance = Appearance()
        lighting_model = LightingModel()
        scattering = ONeilScattering(atmosphere=True, calc_in_fragment=atm_calc_in_fragment, normalize=atm_normalize, hdr=atm_hdr)
        shader = BasicShader(lighting_model=lighting_model, scattering=scattering)
        shape, extra = ShapeYamlParser.decode(data.get('shape', {'icosphere': {'subdivisions': 5}}))
        atmosphere = ONeilAtmosphere(shape=shape,
                                     mie_phase_asymmetry=mie_phase_asymmetry, mie_coef=mie_coef,
                                     rayleigh_coef=rayleigh_coef, sun_power=sun_power,
                                     wavelength=wavelength,
                                     exposure=exposure,
                                     calc_in_fragment=calc_in_fragment,
                                     normalize=normalize,
                                     hdr=hdr,
                                     appearance=appearance, shader=shader)
        return atmosphere

class AtmosphereYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        if data is None: return NoAtmosphere()
        (object_type, parameters) = cls.get_type_and_data(data)
        if object_type == 'oneil':
            return ONeilAtmosphereYamlParser.decode(parameters)
        elif object_type == 'celestia':
            return CelestiaAtmosphereYamlParser.decode(parameters)
        else:
            print("Atmosphpere type", object_type, "unknown")
            return NoAtmosphere()

