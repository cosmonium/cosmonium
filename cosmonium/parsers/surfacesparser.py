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
from .. import settings

from .yamlparser import YamlModuleParser
from .utilsparser import DistanceUnitsYamlParser
from .shapesparser import ShapeYamlParser
from .appearancesparser import AppearanceYamlParser
from .shadersparser import LightingModelYamlParser
from .noiseparser import NoiseYamlParser
from .textureparser import TextureControlYamlParser, HeightColorControlYamlParser

from math import pi

class SurfaceYamlParser(YamlModuleParser):
    @classmethod
    def decode_filtering(cls, data):
        if data == 'none':
            filtering = HeightmapDataSource.F_none
        elif data == 'linear':
            filtering = HeightmapDataSource.F_improved_linear
        elif data == 'quintic':
            filtering = HeightmapDataSource.F_quintic
        elif data == 'bspline':
            filtering = HeightmapDataSource.F_bspline
        else:
            print("Unknown heightmap filtering", data)
            filtering = HeightmapDataSource.F_none
        return filtering

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
                shape.set_lod_control(VertexSizePatchLodControl(settings.max_vertex_size_patch))
            else:
                shape.set_lod_control(TextureOrVertexSizePatchLodControl(settings.max_vertex_size_patch))
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
                filtering = self.decode_filtering(heightmap.get('filter', 'none'))
                height_scale = raw_height_scale * height_scale_units
                relative_height_scale = height_scale / radius
                noise_parser = NoiseYamlParser(scale_length)
                noise = noise_parser.decode(heightmap.get('noise'))
                if shape.patchable:
                    heightmap = PatchedHeightmap(name, size, relative_height_scale, pi, pi, median, ShaderHeightmapPatchFactory(noise))
                    heightmap_source_type = PatchedGpuTextureSource
                    heightmap.global_scale = 1.0 / raw_height_scale
                else:
                    heightmap = ShaderHeightmap(name, size, size // 2, relative_height_scale, median, noise)
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
                #TODO: Should be retrieve from registry
                filtering = HeightmapDataSource.F_none
            control = data.get('control', None)
            if control is not None:
                control_type = control.get('type', 'textures')
                if control_type == 'textures':
                    control_parser = TextureControlYamlParser()
                    control = control_parser.decode(control, height_scale, radius)
                    appearance_source = TextureDictionaryDataSource(appearance)
                elif control_type == 'colormap':
                    control_parser = HeightColorControlYamlParser()
                    control = control_parser.decode(control, height_scale, radius, median)
                    appearance_source = None
                else:
                    print("Unknown control type '%'" % control_type)
                shader_appearance = DetailMap(control, heightmap, create_normals=True)
            else:
                shader_appearance = None
                appearance_source = PandaTextureDataSource()
            data_source = [HeightmapDataSource(heightmap, heightmap_source_type, filtering=filtering)]
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

