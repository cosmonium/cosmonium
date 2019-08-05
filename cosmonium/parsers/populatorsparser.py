from __future__ import print_function
from __future__ import absolute_import

from ..astro import units
from .. import settings

from .yamlparser import YamlModuleParser
from ..procedural.populator import RandomObjectPlacer
from cosmonium.procedural.populator import MultiTerrainPopulator,\
    CpuTerrainPopulator, GpuTerrainPopulator
from cosmonium.parsers.shapesparser import ShapeYamlParser
from cosmonium.parsers.appearancesparser import AppearanceYamlParser
from cosmonium.shaders import BasicShader
from cosmonium.procedural.terrain import TerrainObject

class TerrainObjectYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        shape, extra = ShapeYamlParser.decode(data.get('shape'))
        appearance = AppearanceYamlParser.decode(data.get('appearance'), shape)
        shader = BasicShader(use_model_texcoord=not extra.get('create_uv', False))
        terrain_object = TerrainObject(shape=shape, appearance = appearance, shader=shader)
        return terrain_object

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
    def decode_populator(cls, data):
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
        shader = BasicShader(#lighting_model=lighting_model,
                             #scattering=scattering,
                             use_model_texcoord=not extra.get('create_uv', False))
        object_template = TerrainObject(shape=shape, appearance=appearance, shader=shader)
        placer = PlacerYamlParser.decode(populator_data.get('placer', None))
        if populator_type == 'cpu':
            populator = CpuTerrainPopulator(object_template, density, max_instances, placer)
        elif populator_type == 'gpu':
            populator = GpuTerrainPopulator(object_template, density, max_instances, placer)
        else:
            print("Unknown populator", populator_type, populator_data)
        return populator

    @classmethod
    def decode(self, data):
        populator = None
        if isinstance(data, list):
            populators = []
            for entry in data:
                populators.append(self.decode(entry))
            populator = MultiTerrainPopulator(populators)
        else:
            populator = self.decode_populator(data) 
        return populator
