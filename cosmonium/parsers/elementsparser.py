from __future__ import print_function
from __future__ import absolute_import

from ..bodyelements import Clouds, Ring
from ..shaders import BasicShader

from .yamlparser import YamlModuleParser
from .appearancesparser import AppearanceYamlParser
from .shapesparser import ShapeYamlParser

class CloudsYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data, atmosphere):
        if data is None: return None
        height = float(data.get('height'))
        shape, extra = ShapeYamlParser.decode(data.get('shape'))
        appearance = AppearanceYamlParser.decode(data.get('appearance'), shape)
        lighting_model = None
        scattering = atmosphere.create_scattering_shader(atmosphere=False, calc_in_fragment=False, normalize=False)
        shader = BasicShader(lighting_model=lighting_model, scattering=scattering)
        clouds = Clouds(height, appearance, shader, shape)
        return clouds

class RingsYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        if data is None: return None
        inner_radius = data.get('inner-radius')
        outer_radius = data.get('outer-radius')
        appearance = AppearanceYamlParser.decode(data.get('appearance'), None)
        lighting_model = None
        shader = BasicShader(lighting_model=lighting_model)
        rings = Ring(inner_radius, outer_radius, appearance, shader)
        return rings

