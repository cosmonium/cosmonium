from __future__ import print_function
from __future__ import absolute_import

from ..astro import units
from .. import settings

from .yamlparser import YamlModuleParser
from ..procedural.populator import RandomObjectPlacer
from cosmonium.procedural.populator import CpuTerrainPopulator, GpuTerrainPopulator
from cosmonium.parsers.shapesparser import ShapeYamlParser
from cosmonium.parsers.appearancesparser import AppearanceYamlParser
from cosmonium.shaders import BasicShader
from cosmonium.parsers.shadersparser import VertexControlYamlParser
from cosmonium.shapes import ShapeObject

class PlacerYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data, default='random'):
        placer = None
        extra = {}
        (placer_type, placer_data) = self.get_type_and_data(data, default)
        if placer_type == 'random':
            placer = RandomObjectPlacer()
        else:
            print("Unknown placer", placer_type)
        return placer

class PopulatorYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        if settings.allow_instancing:
            default = 'gpu'
        else:
            default = 'cpu'
        (populator_type, populator_data) = cls.get_type_and_data(data, default)
        populator = None
        density = data.get('density', 250)
        density /= 1000000.0
        max_instances = 250
        shape, extra = ShapeYamlParser.decode(populator_data.get('shape', None))
        appearance = AppearanceYamlParser.decode(populator_data.get('appearance', None), shape)
        vertex_control = VertexControlYamlParser.decode(populator_data.get('vertex', None))
        shader = BasicShader(#lighting_model=lighting_model,
                             #scattering=scattering,
                             geometry_control=vertex_control,
                             use_model_texcoord=not extra.get('create_uv', False))
        object_template = ShapeObject('template', shape=shape, appearance=appearance, shader=shader)
        placer = PlacerYamlParser.decode(populator_data.get('placer', None))
        if populator_type == 'cpu':
            populator = CpuTerrainPopulator(object_template, density, max_instances, placer)
        elif populator_type == 'gpu':
            populator = GpuTerrainPopulator(object_template, density, max_instances, placer)
        else:
            print("Unknown populator", populator_type, populator_data)
        return populator
