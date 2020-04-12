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
from ..procedural.heightmap import PatchedHeightmap, heightmapRegistry
from ..procedural.shaderheightmap import ShaderHeightmap, ShaderHeightmapPatchFactory
from ..procedural.interpolator import NearestInterpolator, BilinearInterpolator, ImprovedBilinearInterpolator, QuinticInterpolator, BSplineInterpolator

from .yamlparser import YamlModuleParser
from .objectparser import ObjectYamlParser
from .utilsparser import DistanceUnitsYamlParser
from .noiseparser import NoiseYamlParser

from math import pi

class InterpolatorYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        interpolator = None
        (object_type, parameters) = self.get_type_and_data(data, 'bilinear')
        if object_type == 'nearest':
            interpolator = NearestInterpolator()
        elif object_type == 'bilinear':
            interpolator = BilinearInterpolator()
        elif object_type == 'improved-bilinear':
            interpolator = ImprovedBilinearInterpolator()
        elif object_type == 'quintic':
            interpolator = QuinticInterpolator()
        elif object_type == 'bspline':
            interpolator = BSplineInterpolator()
        else:
            print("Unknown interpolator", object_type)
        return interpolator

class HeightmapYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data, name, patched, radius):
        size = data.get('size', 256)
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
                relative_height_scale = height_scale / radius
        else:
            height_scale = raw_height_scale
            scale_length = 1.0
            relative_height_scale = height_scale
        median = data.get('median', True)
        interpolator = InterpolatorYamlParser.decode(data.get('interpolator'))
        noise_parser = NoiseYamlParser(scale_length)
        noise = noise_parser.decode(data.get('noise'))
        if patched:
            max_lod = data.get('max-lod', 100)
            heightmap = PatchedHeightmap(name, size,
                                         relative_height_scale, pi, pi, median,
                                         ShaderHeightmapPatchFactory(noise), interpolator, max_lod)
        else:
            heightmap = ShaderHeightmap(name, size, size // 2, relative_height_scale, median, noise, interpolator)
        #TODO: should be set using a method or in constructor
        #TODO: Why raw_height_scale ???
        heightmap.global_scale = 1.0 / raw_height_scale
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
