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
from ..heightmap import TextureHeightmap, TexturePatchedHeightmap, heightmapRegistry
from ..interpolators import HardwareInterpolator, SoftwareInterpolator
from ..filters import NearestFilter, BilinearFilter, SmoothstepFilter, QuinticFilter, BSplineFilter
from ..procedural.shaderheightmap import HeightmapPatchGenerator, ShaderPatchedHeightmap
from ..textures import HeightMapTexture

from .yamlparser import YamlModuleParser
from .objectparser import ObjectYamlParser
from .utilsparser import DistanceUnitsYamlParser
from .noiseparser import NoiseYamlParser
from .texturesourceparser import TextureSourceYamlParser

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
        min_height = data.get('min-height', None)
        max_height = data.get('max-height', None)
        height_scale = data.get('height-scale', 1.0)
        height_offset = data.get('height-offset', 0.0)
        if min_height is not None:
            min_height_units = DistanceUnitsYamlParser.decode(data.get('min-height-units'), units.m)
            min_height *= min_height_units
        if max_height is not None:
            max_height_units = DistanceUnitsYamlParser.decode(data.get('max-height-units'), units.m)
            max_height *= max_height_units
        height_scale_units = DistanceUnitsYamlParser.decode(data.get('height-scale-units'), units.m)
        height_scale *= height_scale_units
        height_offset_units = DistanceUnitsYamlParser.decode(data.get('height-offset-units'), units.m)
        height_offset *= height_offset_units
        if min_height is None:
            if max_height is None:
                min_height = -(height_scale + height_offset)
                max_height = height_scale + height_offset
            else:
                min_height = - max_height
        else:
            if max_height is None:
                max_height = -min_height
        if radius is not None:
            scale_length = data.get('scale-length', None)
            scale_length_units = DistanceUnitsYamlParser.decode(data.get('scale-length-units'), units.m)
            if scale_length is not None:
                scale_length *= scale_length_units
            else:
                scale_length = radius * 2 * pi
            min_height /= radius
            max_height /= radius
            height_scale /= radius
            height_offset /= radius
        else:
            scale_length = 1.0
        interpolator = InterpolatorYamlParser.decode(data.get('interpolator'))
        filter = FilterYamlParser.decode(data.get('filter'))
        if heightmap_type == 'procedural':
            size = data.get('size', 256)
            overlap = data.get('overlap', 1)
            noise_parser = NoiseYamlParser(scale_length)
            func = data.get('func')
            if func is None:
                func = data.get('noise')
                print("Warning: 'noise' entry is deprecated, use 'func' instead'")
            heightmap_function = noise_parser.decode(func)
            heightmap_data_source = HeightmapPatchGenerator(size, size, heightmap_function, 1.0)
            #TODO: The actual heightmap class is parametric until heightmaps are also a data source like the textures 
            heightmap_class = ShaderPatchedHeightmap
        else:
            heightmap_data = data.get('data')
            overlap = data.get('overlap', 0)
            if heightmap_data is not None:
                texture_source, texture_offset = TextureSourceYamlParser.decode(heightmap_data)
                heightmap_data_source = HeightMapTexture(texture_source)
                #TODO: missing texture offset
                if patched:
                    heightmap_class = TexturePatchedHeightmap
                    size = heightmap_data_source.source.texture_size
                else:
                    size = 1.0
        if patched:
            max_lod = data.get('max-lod', 100)
            heightmap = heightmap_class(name, heightmap_data_source, size,
                                        min_height, max_height, height_scale, height_offset,
                                        1.0, 1.0, overlap,
                                        interpolator, filter, max_lod)
        else:
            heightmap = TextureHeightmap(name, size, size / 2,
                                         min_height, max_height, height_scale, height_offset,
                                         heightmap_data_source, interpolator, filter)
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
