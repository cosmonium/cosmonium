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

from ..surfaces import FlatSurface, HeightmapSurface
from ..surfaces import surfaceCategoryDB, SurfaceCategory
from ..shaders import BasicShader, PandaTextureDataSource
from ..patchedshapes import VertexSizePatchLodControl, TextureOrVertexSizePatchLodControl
from ..shapes import MeshShape
from ..astro import units
from ..procedural.shaders import DisplacementVertexControl, HeightmapDataSource, DetailMap, TextureDictionaryDataSource
from ..procedural.textures import GpuTextureSource, PatchedGpuTextureSource
from ..procedural.heightmap import PatchedHeightmap, heightmapRegistry
from ..procedural.shaderheightmap import ShaderHeightmap, ShaderHeightmapPatchFactory
from ..catalogs import objectsDB
from .. import settings

from .yamlparser import YamlModuleParser
from .objectparser import ObjectYamlParser
from .utilsparser import DistanceUnitsYamlParser
from .shapesparser import ShapeYamlParser
from .appearancesparser import AppearanceYamlParser
from .shadersparser import LightingModelYamlParser
from .noiseparser import NoiseYamlParser
from .heightmapsparser import InterpolatorYamlParser
from .textureparser import TextureControlYamlParser

from math import pi

class SurfaceYamlParser(YamlModuleParser):
    @classmethod
    def decode_surface(self, data, atmosphere, previous, owner):
        name = data.get('name', None)
        category_name = data.get('category', 'visible')
        category = surfaceCategoryDB.get(category_name)
        if category is None:
            print("Category '%s' unknown" % category_name)
            category = SurfaceCategory(category_name)
            surfaceCategoryDB.add(category)
        resolution = data.get('resolution', None)
        attribution = data.get('attribution', data.get('source'))
        #The next parameters are using set_default in order to propagate
        #their manual configuration to the next surface, if any.
        heightmap = data.setdefault('heightmap', previous.get('heightmap'))
        shape = data.setdefault('shape', previous.get('shape'))
        appearance = data.setdefault('appearance', previous.get('appearance'))
        lighting_model = data.setdefault('lighting-model', previous.get('lighting-model'))
        if shape is not None:
            shape, extra = ShapeYamlParser.decode(shape)
        if appearance is not None:
            appearance = AppearanceYamlParser.decode(appearance)
        if shape is None:
            recommended_shape = None
            if heightmap is not None:
                recommended_shape = 'sqrt-sphere'
            elif appearance is not None:
                recommended_shape = appearance.get_recommended_shape()
            if recommended_shape is None:
                recommended_shape = 'patched-sphere'
            shape, extra = ShapeYamlParser.decode(recommended_shape)
        if appearance is None:
            if isinstance(shape, MeshShape):
                appearance = 'model'
            else:
                appearance = 'textures'
            appearance = AppearanceYamlParser.decode(appearance)
        lighting_model = LightingModelYamlParser.decode(lighting_model, appearance)
        if shape.patchable:
            if appearance.texture is None or appearance.texture.source.procedural:
                shape.set_lod_control(VertexSizePatchLodControl(settings.patch_max_vertex_size,
                                                                density=settings.patch_constant_density))
            else:
                shape.set_lod_control(TextureOrVertexSizePatchLodControl(settings.patch_max_vertex_size,
                                                                         min_density=settings.patch_min_density,
                                                                         density=settings.patch_max_density))
        if heightmap is None:
            shader = BasicShader(lighting_model=lighting_model,
                                 use_model_texcoord=not extra.get('create-uv', False))
            surface = FlatSurface(name, category=category, resolution=resolution, attribution=attribution,
                                  shape=shape, appearance=appearance, shader=shader)
        else:
            radius = owner.get('radius')
            if isinstance(heightmap, dict):
                #TODO: Refactor with HeightmapYamlParser !
                name = data.get('name', 'heightmap')
                size = heightmap.get('size', 256)
                raw_height_scale = heightmap.get('max-height', 1.0)
                height_scale_units = DistanceUnitsYamlParser.decode(data.get('max-height'), units.m)
                scale_length = heightmap.get('scale-length', None)
                scale_length_units = DistanceUnitsYamlParser.decode(data.get('scale-length-units'), units.m)
                if scale_length is not None:
                    scale_length *= scale_length_units
                else:
                    scale_length = radius * 2 * pi
                median = heightmap.get('median', True)
                interpolator = InterpolatorYamlParser.decode(heightmap.get('interpolator'))
                height_scale = raw_height_scale * height_scale_units
                relative_height_scale = height_scale / radius
                noise_parser = NoiseYamlParser(scale_length)
                noise = noise_parser.decode(heightmap.get('noise'))
                if shape.patchable:
                    max_lod = heightmap.get('max-lod', 100)
                    heightmap = PatchedHeightmap(name, size,
                                                 relative_height_scale, pi, pi, median,
                                                 ShaderHeightmapPatchFactory(noise), interpolator, max_lod)
                    heightmap_source_type = PatchedGpuTextureSource
                    heightmap.global_scale = 1.0 / raw_height_scale
                else:
                    heightmap = ShaderHeightmap(name, size, size // 2, relative_height_scale, median, noise, interpolator)
                    heightmap_source_type = GpuTextureSource
                #TODO: should be set using a method or in constructor
                heightmap.global_scale = 1.0 / raw_height_scale
            else:
                if shape.patchable:
                    heightmap = heightmapRegistry.get(heightmap + '-patched')
                    heightmap_source_type = PatchedGpuTextureSource
                else:
                    heightmap = heightmapRegistry.get(heightmap)
                    heightmap_source_type = GpuTextureSource
            control = data.get('control', None)
            if control is not None:
                control_parser = TextureControlYamlParser()
                (control, appearance_source) = control_parser.decode(control, appearance, heightmap.height_scale, radius, heightmap.median)
                if control is not None:
                    shader_appearance = DetailMap(control, heightmap, create_normals=True)
            else:
                shader_appearance = None
                appearance_source = PandaTextureDataSource()
            data_source = [HeightmapDataSource(heightmap, heightmap_source_type)]
            if appearance_source is not None:
                data_source.append(appearance_source)
            shader = BasicShader(vertex_control=DisplacementVertexControl(heightmap),
                                 data_source=data_source,
                                 appearance=shader_appearance,
                                 lighting_model=lighting_model,
                                 use_model_texcoord=not extra.get('create-uv', False))
            surface = HeightmapSurface(name, radius=radius,
                                       #category=category, resolution=resolution, source=source,
                                       shape=shape, heightmap=heightmap, biome=None, appearance=appearance, shader=shader)
        if atmosphere is not None:
            atmosphere.add_shape_object(surface)
        return surface

    @classmethod
    def decode(self, data, atmosphere, owner):
        surfaces = []
        #TODO: Should do surface element cloning instead of reparsing
        previous = {}
        for entry in data:
            surface = self.decode_surface(entry, atmosphere, previous, owner)
            surfaces.append(surface)
            previous = entry
        return surfaces

class StandaloneSurfaceYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        name = data.get('name', None)
        parent_name = data.get('parent')
        parent = objectsDB.get(parent_name)
        if parent is None:
            print("ERROR: Parent '%s' of surface '%s' not found" % (parent_name, name))
            return None
        active = data.get('active', 'True')
        surface = SurfaceYamlParser.decode_surface(data, parent.atmosphere, {}, parent)
        parent.add_surface(surface)
        if active:
            parent.set_surface(surface)
        return None

ObjectYamlParser.register_object_parser('surface', StandaloneSurfaceYamlParser())
