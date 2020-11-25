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

from __future__ import print_function
from __future__ import absolute_import

from ..astro import units
from ..heightmap import TextureHeightmap, TextureHeightmapPatchFactory, PatchedHeightmap, heightmapRegistry
from ..interpolators import HardwareInterpolator, SoftwareInterpolator
from ..filters import NearestFilter, BilinearFilter, SmoothstepFilter, QuinticFilter, BSplineFilter
from ..procedural.shaderheightmap import ShaderHeightmap, ShaderHeightmapPatchFactory
from ..textures import HeightMapTexture

from .yamlparser import YamlModuleParser
from .objectparser import ObjectYamlParser
from .utilsparser import DistanceUnitsYamlParser
from .noiseparser import NoiseYamlParser
from .appearancesparser import TexturesAppearanceYamlParser

from math import pi

class InterpolatorYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        interpolator = None
        (object_type, parameters) = self.get_type_and_data(data, 'hardware')
        if object_type == 'hardware':
            interpolator = HardwareInterpolator()
        elif object_type == 'software':
            interpolator = SoftwareInterpolator()
        else:
            print("Unknown interpolator", object_type)
        return interpolator

class FilterYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        filter = None
        (object_type, parameters) = self.get_type_and_data(data, 'bilinear')
        if object_type == 'nearest':
            filter = NearestFilter()
        elif object_type == 'bilinear':
            filter = BilinearFilter()
        elif object_type == 'smoothstep':
            filter = SmoothstepFilter()
        elif object_type == 'quintic':
            filter = QuinticFilter()
        elif object_type == 'bspline':
            filter = BSplineFilter()
        else:
            print("Unknown filter", object_type)
        return filter

class HeightmapYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data, name, patched, radius):
        heightmap_type = data.get('type', 'procedural')
        raw_height_scale = data.get('max-height', 1.0)
        if radius is not None:
            height_scale_units = DistanceUnitsYamlParser.decode(data.get('max-height-units'), units.m)
            height_scale = raw_height_scale * height_scale_units
            scale_length = data.get('scale-length', None)
            scale_length_units = DistanceUnitsYamlParser.decode(data.get('scale-length-units'), units.m)
            if scale_length is not None:
                scale_length *= scale_length_units
            else:
                scale_length = radius * 2 * pi
            relative_height_scale = height_scale_units / radius
        else:
            height_scale = raw_height_scale
            scale_length = 1.0
            relative_height_scale = height_scale
        median = data.get('median', True)
        interpolator = InterpolatorYamlParser.decode(data.get('interpolator'))
        filter = FilterYamlParser.decode(data.get('filter'))
        factory = None
        if heightmap_type == 'procedural':
            size = data.get('size', 256)
            noise_parser = NoiseYamlParser(scale_length)
            func = data.get('func')
            if func is None:
                func = data.get('noise')
                print("Warning: 'noise' entry is deprecated, use 'func' instead'")
            heightmap_source = noise_parser.decode(func)
            if patched:
                factory = ShaderHeightmapPatchFactory(heightmap_source)
        else:
            heightmap_data = data.get('data')
            if heightmap_data is not None:
                texture_source, texture_offset = TexturesAppearanceYamlParser.decode_source(heightmap_data)
                heightmap_source = HeightMapTexture(texture_source)
                #TODO: missing texture offset
                if patched:
                    factory = TextureHeightmapPatchFactory(heightmap_source)
                    size = heightmap_source.source.texture_size
                else:
                    size = 1.0
        if patched:
            max_lod = data.get('max-lod', 100)
            heightmap = PatchedHeightmap(name, size,
                                         relative_height_scale, pi, pi, median,
                                         factory, interpolator, filter, max_lod)
        else:
            heightmap = TextureHeightmap(name, size, size / 2, relative_height_scale, median, heightmap_source, interpolator, filter)
        return heightmap

class StandaloneHeightmapYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        name = data.get('name')
        if name is None: return None
        heightmap = HeightmapYamlParser.decode(data, name, False, None)
        patched_heightmap = HeightmapYamlParser.decode(data, name, True, None)
        heightmapRegistry.register(name, heightmap)
        heightmapRegistry.register(name + '-patched', patched_heightmap)
        return None

ObjectYamlParser.register_object_parser('heightmap', StandaloneHeightmapYamlParser())
