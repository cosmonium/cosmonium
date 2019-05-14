from __future__ import print_function
from __future__ import absolute_import

from ..bodyelements import NoAtmosphere
from ..shaders import BasicShader, LightingModel
from ..appearances import Appearance
from ..oneil import ONeilScattering, ONeilAtmosphere

from .yamlparser import YamlModuleParser
from .shapesparser import ShapeYamlParser

class ONeilAtmosphereYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        mie_phase_asymmetry = data.get('g', -0.99)
        rayleigh_coef = data.get('rayleigh', 0.0025)
        mie_coef = data.get('mie', 0.0015)
        sun_power = data.get('power', 15.0)
        wavelength = data.get('wavelength', [0.650, 0.570, 0.465])
        appearance = Appearance()
        lighting_model = LightingModel()
        scattering = ONeilScattering(atmosphere=True, calc_in_fragment=True, normalize=True)
        shader = BasicShader(lighting_model=lighting_model, scattering=scattering)
        shape, extra = ShapeYamlParser.decode(data.get('shape', {'icosphere': {'subdivisions': 5}}))
        atmosphere = ONeilAtmosphere(shape=shape,
                                     mie_phase_asymmetry=mie_phase_asymmetry, mie_coef=mie_coef,
                                     rayleigh_coef=rayleigh_coef, sun_power=sun_power,
                                     wavelength=wavelength,
                                     appearance=appearance, shader=shader)
        return atmosphere

class AtmosphereYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        if data is None: return NoAtmosphere()
        (object_type, parameters) = cls.get_type_and_data(data)
        if object_type == 'oneil':
            return ONeilAtmosphereYamlParser.decode(parameters)
        else:
            print("Atmosphpere type", object_type, "unknown")
            return NoAtmosphere()

