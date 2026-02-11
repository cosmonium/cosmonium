#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2026 Laurent Deru.
#
# Cosmonium is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Cosmonium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#


from math import pi

from ..astro import units
from ..filters import BilinearFilter, BSplineFilter, NearestFilter, QuinticFilter, SmoothstepFilter
from ..heightmap import TextureHeightmap, TexturePatchedHeightmap, heightmapRegistry
from ..interpolators import HardwareInterpolator, SoftwareInterpolator
from ..procedural.shaderheightmap import HeightmapPatchGenerator, ShaderPatchedHeightmap
from ..textures import HeightMapTexture
from .noiseparser import NoiseYamlParser
from .objectparser import ObjectYamlParser
from .schemas.heightmap import HeightmapConfig
from .texturesourceparser import TextureSourceYamlParser
from .utilsparser import DistanceUnitsYamlParser
from .yamlparser import TypedYamlParser, YamlModuleParser


class InterpolatorYamlParser(TypedYamlParser):
    @classmethod
    def decode(cls, data):
        interpolator = None
        (object_type, _parameters) = cls.get_type_and_data(data, 'hardware')
        if object_type == 'hardware':
            interpolator = HardwareInterpolator()
        elif object_type == 'software':
            interpolator = SoftwareInterpolator()
        else:
            print("Unknown interpolator", object_type)
        return interpolator


class FilterYamlParser(TypedYamlParser):
    @classmethod
    def decode(cls, data, interpolator):
        filter = None
        (object_type, _parameters) = cls.get_type_and_data(data, 'bilinear')
        if object_type == 'nearest':
            filter = NearestFilter(interpolator)
        elif object_type == 'bilinear':
            filter = BilinearFilter(interpolator)
        elif object_type == 'smoothstep':
            filter = SmoothstepFilter(interpolator)
        elif object_type == 'quintic':
            filter = QuinticFilter(interpolator)
        elif object_type == 'bspline':
            filter = BSplineFilter(interpolator)
        else:
            print("Unknown filter", object_type)
        return filter


class HeightmapYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, name, patched, radius=None, scale=1.0, coord_scale=1.0):
        data = HeightmapConfig.model_validate(data)
        heightmap_type = 'texture' if data.data else 'procedural'
        min_height = data.min_height
        max_height = data.max_height
        height_scale = data.height_scale
        height_offset = data.height_offset
        if min_height is not None:
            min_height *= DistanceUnitsYamlParser.decode(data.min_height_units, units.m)
        if max_height is not None:
            max_height *= DistanceUnitsYamlParser.decode(data.max_height_units, units.m)
        height_scale *= DistanceUnitsYamlParser.decode(data.height_scale_units, units.m)
        height_offset *= DistanceUnitsYamlParser.decode(data.height_offset_units, units.m)
        if min_height is None:
            if max_height is None:
                min_height = -(height_scale + height_offset)
                max_height = height_scale + height_offset
            else:
                min_height = -max_height
        else:
            if max_height is None:
                max_height = -min_height
        if radius is not None:
            if data.scale_length is not None:
                scale_length = data.scale_length * DistanceUnitsYamlParser.decode(data.scale_length_units, units.m)
            else:
                scale_length = radius * 2 * pi
            min_height /= radius
            max_height /= radius
            height_scale /= radius
            height_offset /= radius
        else:
            scale_length = data.scale_length
            if scale_length is None:
                scale_length = 1.0
            scale_length = scale_length * DistanceUnitsYamlParser.decode(data.scale_length_units, units.m)
            min_height /= scale
            max_height /= scale
            height_scale /= scale
            height_offset /= scale
        interpolator = InterpolatorYamlParser.decode(data.interpolator)
        filter = FilterYamlParser.decode(data.filter, interpolator)
        if heightmap_type == 'procedural':
            size = data.size
            overlap = data.overlap
            noise_parser = NoiseYamlParser(scale_length)
            func = data.func
            if func is None:
                func = data.noise
                print("Warning: 'noise' entry is deprecated, use 'func' instead")
            heightmap_function = noise_parser.decode(func)
            heightmap_data_source = HeightmapPatchGenerator(size, size, heightmap_function, coord_scale)
            # TODO: The actual heightmap class is parametric until heightmaps are also a data source like the textures
            heightmap_class = ShaderPatchedHeightmap
        else:
            heightmap_data = data.data
            overlap = data.overlap
            if heightmap_data is not None:
                texture_source, texture_offset = TextureSourceYamlParser.decode(heightmap_data)
                heightmap_data_source = HeightMapTexture(texture_source)
                # TODO: missing texture offset
                if patched:
                    heightmap_class = TexturePatchedHeightmap
                    size = heightmap_data_source.source.texture_size
                else:
                    size = 1.0
        if patched:
            return heightmap_class(
                name,
                heightmap_data_source,
                size,
                min_height,
                max_height,
                height_scale,
                height_offset,
                overlap,
                interpolator,
                filter,
                data.max_lod,
            )
        else:
            return TextureHeightmap(
                name,
                size,
                size / 2,
                min_height,
                max_height,
                height_scale,
                height_offset,
                heightmap_data_source,
                interpolator,
                filter,
            )


class StandaloneHeightmapYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        data = HeightmapConfig.model_validate(data)
        name = data.name
        heightmap = HeightmapYamlParser.decode(data, name, False, None)
        patched_heightmap = HeightmapYamlParser.decode(data, name, True, None)
        heightmapRegistry.register(name, heightmap)
        heightmapRegistry.register(name + '-patched', patched_heightmap)
        return None


def register_heightmap_parsers():
    ObjectYamlParser.register_object_parser('heightmap', StandaloneHeightmapYamlParser())
