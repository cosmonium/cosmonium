from __future__ import print_function
from __future__ import absolute_import

from ..surfaces import FlatSurface, HeightmapSurface
from ..surfaces import surfaceCategoryDB, SurfaceCategory
from ..shaders import BasicShader, PandaTextureDataSource
from ..patchedshapes import VertexSizePatchLodControl
from ..astro import units
from ..procedural.shaders import DisplacementGeometryControl, HeightmapDataSource, DetailMap, TextureDictionaryDataSource
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
        source = data.get('source', None)
        heightmap = data.get('heightmap', previous.get('heightmap'))
        if heightmap is not None:
            default_shape = 'sqrt-sphere'
        else:
            default_shape = 'patched-sphere'
        shape = data.setdefault('shape', previous.get('shape', default_shape))
        appearance = data.setdefault('appearance', previous.get('appearance'))
        lighting_model = data.setdefault('lighting-model', previous.get('lighting-model'))
        shape, extra = ShapeYamlParser.decode(shape)
        appearance = AppearanceYamlParser.decode(appearance, shape)
        lighting_model = LightingModelYamlParser.decode(lighting_model, appearance)
        scattering = atmosphere.create_scattering_shader(atmosphere=False, calc_in_fragment=True, normalize=True)
        if appearance.texture is None and shape.patchable:
            shape.set_lod_control(VertexSizePatchLodControl(settings.max_vertex_size_patch))
        if heightmap is None:
            shader = BasicShader(lighting_model=lighting_model,
                                 scattering=scattering,
                                 use_model_texcoord=not extra.get('create_uv', False))
            surface = FlatSurface(name, category=category, resolution=resolution, source=source,
                                  shape=shape, appearance=appearance, shader=shader)
        else:
            radius = owner.get('radius')
            if isinstance(heightmap, dict):
                #TODO: Refactor with HeightmapYamlParser !
                name = data.get('name', 'heightmap')
                size = heightmap.get('size', 256)
                height_scale = heightmap.get('scale', 1.0)
                scale_units = DistanceUnitsYamlParser.decode(data.get('scale-units'), units.m)
                scale_length = heightmap.get('scale-length', None)
                scale_length_units = DistanceUnitsYamlParser.decode(data.get('scale-length-units'), units.m)
                if scale_length is not None:
                    scale_length *= scale_length_units
                else:
                    scale_length = radius * 2 * pi
                scale_noise = heightmap.get('scale-noise', True)
                median = heightmap.get('median', True)
                filtering = self.decode_filtering(heightmap.get('filter', 'none'))
                height_scale *= scale_units
                if scale_noise:
                    noise_scale = 1.0 / height_scale
                else:
                    noise_scale = 1.0
                scale = height_scale / radius
                noise_parser = NoiseYamlParser(noise_scale * scale_units, scale_length)
                noise = noise_parser.decode(heightmap.get('noise'))
                noise_offset = None
                noise_scale = None
                if shape.patchable:
                    heightmap = PatchedHeightmap(name, size, scale, pi, pi, median, ShaderHeightmapPatchFactory(noise))
                    heightmap_source_type = PatchedGpuTextureSource
                else:
                    heightmap = ShaderHeightmap(name, size, size // 2, scale, median, noise, noise_offset, noise_scale)
                    heightmap_source_type = GpuTextureSource
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
                    appearance_source = TextureDictionaryDataSource(appearance, TextureDictionaryDataSource.F_hash)
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
            shader = BasicShader(geometry_control=DisplacementGeometryControl(heightmap),
                                 data_source=data_source,
                                 appearance=shader_appearance,
                                 lighting_model=lighting_model,
                                 scattering=scattering,
                                 use_model_texcoord=not extra.get('create_uv', False))
            surface = HeightmapSurface(name, radius=radius,
                                       #category=category, resolution=resolution, source=source,
                                       shape=shape, heightmap=heightmap, biome=None, appearance=appearance, shader=shader)
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

