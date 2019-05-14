from __future__ import print_function
from __future__ import absolute_import

from ..astro import units
from ..procedural.heightmap import PatchedHeightmap, heightmapRegistry
from ..procedural.shaderheightmap import ShaderHeightmap, ShaderHeightmapPatchFactory

from .yamlparser import YamlModuleParser
from .objectparser import ObjectYamlParser
from .utilsparser import DistanceUnitsYamlParser
from .noiseparser import NoiseYamlParser

from math import pi

class HeightmapYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        name = data.get('name')
        if name is None: return None
        size = data.get('size', 256)
        scale = data.get('scale', 1.0)
        scale_units = DistanceUnitsYamlParser.decode(data.get('scale-units'), units.Km)
        median = data.get('median', True)
        noise_parser = NoiseYamlParser()
        noise = noise_parser.decode(data.get('noise'))
        noise_offset = None
        noise_scale = None
        scale *= scale_units
        patched_heightmap = PatchedHeightmap(name, size, scale, pi, pi, median, ShaderHeightmapPatchFactory(noise))
        heightmap = ShaderHeightmap(name, size, size // 2, scale, median, noise, noise_offset, noise_scale)
        heightmapRegistry.register(name, heightmap)
        heightmapRegistry.register(name + '-patched', patched_heightmap)
        return None

ObjectYamlParser.register_object_parser('heightmap', HeightmapYamlParser())
