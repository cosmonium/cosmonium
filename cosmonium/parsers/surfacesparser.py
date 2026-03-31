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


from math import sqrt

from .. import settings
from ..catalogs import objectsDB
from ..components.elements.surface_categories import SurfaceCategory, surfaceCategoryDB
from ..components.elements.surfaces import (
    EllipsoidFlatSurface,
    FlatSurface,
    HeightmapFlatSurface,
    HeightmapSurface,
    MeshSurface,
)
from ..heightmap import heightmapRegistry
from ..opengl import OpenGLConfig
from ..patchedshapes.lodcontrol import (
    TextureOrVertexSizeLodControl,
    VertexSizeLodControl,
    VertexSizeMaxDistanceLodControl,
)
from ..patchedshapes.tiles import GpuPatchTerrainLayerFactory, MeshTerrainLayerFactory, TileFactory
from ..shaders.rendering import RenderingShader
from ..shaders.tessellation import ConstantTessellationControl
from ..shaders.vertex_control.displacement import DisplacementVertexControl
from ..shapes.mesh import MeshShape
from .appearancesparser import AppearanceYamlParser
from .heightmapsparser import HeightmapYamlParser
from .objectparser import ObjectYamlParser
from .schemas.surface import FlatSurfaceConfig, StandaloneSurfaceConfig, SurfaceConfig
from .shadersparser import LightingModelYamlParser
from .shapesparser import ShapeYamlParser
from .utilsparser import get_radius_scale
from .yamlparser import YamlModuleParser


class SurfaceYamlParser(YamlModuleParser):
    @classmethod
    def decode_surface(self, data, previous, owner):
        if isinstance(data, SurfaceConfig):
            # Already validated - use model directly (no cascading needed)
            config = data
        else:
            # Cascade defaults from previous surface (must happen on the raw dict before validation)
            data.setdefault('heightmap', previous.get('heightmap'))
            data.setdefault('shape', previous.get('shape'))
            data.setdefault('appearance', previous.get('appearance'))
            data.setdefault('lighting-model', previous.get('lighting-model'))
            # Validate through the schema (after cascaded defaults are in the dict)
            config = SurfaceConfig.model_validate(data)

        name = config.name
        category_name = config.category or 'visible'
        category = surfaceCategoryDB.get(category_name)
        if category is None:
            print("Category '%s' unknown" % category_name)
            category = SurfaceCategory(category_name)
            surfaceCategoryDB.add(category)
        resolution = config.resolution
        attribution = config.attribution or config.source
        radius, ellipticity, scale = get_radius_scale(config, owner)
        heightmap_data = config.heightmap
        shape = config.shape
        appearance = config.appearance
        lighting_model = config.lighting_model
        if shape is None and heightmap_data is not None:
            shape = 'sqrt-sphere'
        if shape is not None:
            shape, extra = ShapeYamlParser.decode(shape, radius=radius)
        if heightmap_data is not None:
            if isinstance(heightmap_data, dict):
                name = config.name or 'heightmap'
                heightmap = HeightmapYamlParser.decode(heightmap_data, name, shape.patchable, radius)
            else:
                if shape.patchable:
                    heightmap = heightmapRegistry.get(heightmap_data + '-patched')
                else:
                    heightmap = heightmapRegistry.get(heightmap_data)
        else:
            heightmap = None
        if appearance is not None:
            appearance = AppearanceYamlParser.decode(appearance, heightmap, radius)
        if shape is None:
            recommended_shape = None
            if appearance is not None:
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
        shader_appearance = appearance.get_shader_appearance()
        if shape.is_spherical():
            if shape.patchable:
                if appearance.texture is None or appearance.texture.source.procedural:
                    shape.set_lod_control(
                        VertexSizeLodControl(settings.patch_max_vertex_size, density=settings.patch_default_density)
                    )
                else:
                    shape.set_lod_control(
                        TextureOrVertexSizeLodControl(
                            settings.patch_max_vertex_size,
                            density=settings.patch_default_density,
                        )
                    )
            if heightmap is None:
                shader = RenderingShader(
                    lighting_model=lighting_model,
                    appearance=shader_appearance,
                    use_model_texcoord=not extra.get('create-uv', False),
                )
                surface = EllipsoidFlatSurface(
                    name,
                    category=category,
                    resolution=resolution,
                    attribution=attribution,
                    radius=radius,
                    oblateness=ellipticity,
                    scale=scale,
                    shape=shape,
                    appearance=appearance,
                    shader=shader,
                )
            else:
                data_source = []
                shape_data_source = shape.get_shader_data_source()
                if shape_data_source is not None:
                    data_source.append(shape_data_source)
                # TODO: The configuration of the data store can not be done like that
                if shape.data_store is not None:
                    data_source.append(shape.data_store.get_shader_data_source())
                data_source.append(heightmap.get_data_source(shape.data_store is not None))
                appearance_source = appearance.get_data_source()
                if appearance_source is not None:
                    data_source.append(appearance_source)
                shader = RenderingShader(
                    vertex_control=DisplacementVertexControl(heightmap),
                    data_source=data_source,
                    appearance=shader_appearance,
                    lighting_model=lighting_model,
                    use_model_texcoord=not extra.get('create-uv', False),
                )
                surface = HeightmapSurface(
                    name,
                    # category=category, resolution=resolution, source=source,
                    radius=radius,
                    oblateness=ellipticity,
                    scale=scale,
                    height_scale=radius,
                    shape=shape,
                    heightmap=heightmap,
                    biome=None,
                    appearance=appearance,
                    shader=shader,
                )
        else:
            shader = RenderingShader(
                lighting_model=lighting_model,
                appearance=shader_appearance,
                use_model_texcoord=not extra.get('create-uv', False),
            )
            surface = MeshSurface(
                name,
                category=category,
                resolution=resolution,
                attribution=attribution,
                shape=shape,
                appearance=appearance,
                shader=shader,
            )
        return surface

    @classmethod
    def decode(cls, data, owner):
        surfaces = []
        # TODO: Should do surface element cloning instead of reparsing
        previous = {}
        for entry in data:
            surface = cls.decode_surface(entry, previous, owner)
            surfaces.append(surface)
            previous = entry
        return surfaces


class FlatSurfaceParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        config = FlatSurfaceConfig.model_validate(data)
        tile_size = config.tile_size
        # TODO: coord_scale should simply be tile_size
        coord_scale = tile_size / 16384
        max_vertex_size = config.max_vertex_size
        max_lod = config.max_lod
        max_distance = config.max_distance if config.max_distance is not None else 1.001 * tile_size * sqrt(2)
        tile_density = config.tile_density if config.tile_density is not None else settings.patch_default_density
        hw_tessellation = config.hw_tessellation

        shape_data = config.shape
        appearance = config.appearance
        lighting_model = config.lighting_model
        heightmap_data = config.heightmap
        biome_data = config.biome

        if shape_data is None:
            shape_data = {'type': 'tiled-plane'}
        shape_data['tile-size'] = tile_size
        shape, extra = ShapeYamlParser.decode(shape_data)

        if heightmap_data is not None:
            heightmap = HeightmapYamlParser.decode(
                heightmap_data, 'heightmap', patched=True, scale=tile_size, coord_scale=coord_scale
            )
        else:
            heightmap = None
        if biome_data is not None:
            biome = HeightmapYamlParser.decode(
                biome_data, 'biome', patched=True, scale=tile_size, coord_scale=coord_scale
            )
        else:
            biome = None

        if appearance is not None:
            appearance = AppearanceYamlParser.decode(appearance, heightmap=heightmap, radius=1.0)
        if appearance is None:
            if isinstance(shape, MeshShape):
                appearance = 'model'
            else:
                appearance = 'textures'
            appearance = AppearanceYamlParser.decode(appearance)
        lighting_model = LightingModelYamlParser.decode(lighting_model, appearance)
        shader_appearance = appearance.get_shader_appearance()

        if shape.is_spherical():
            if shape.patchable:
                if hw_tessellation and OpenGLConfig.hardware_tessellation:
                    terrain_layer_factory = GpuPatchTerrainLayerFactory()
                else:
                    terrain_layer_factory = MeshTerrainLayerFactory()
                factory = TileFactory(heightmap, tile_density, tile_size, terrain_layer_factory)
                lod_control = VertexSizeMaxDistanceLodControl(
                    max_distance / tile_size, max_vertex_size, density=tile_density, max_lod=max_lod
                )
                shape.set_factory(factory, heightmap, lod_control)
                shape.set_lod_control(lod_control)
            if heightmap is None:
                shader = RenderingShader(
                    lighting_model=lighting_model,
                    appearance=shader_appearance,
                    use_model_texcoord=not extra.get('create-uv', False),
                )
                surface = FlatSurface('surface', shape, appearance, shader, clickable=False)
            else:
                data_source = []
                shape_data_source = shape.get_shader_data_source()
                if shape_data_source is not None:
                    data_source.append(shape_data_source)
                # TODO: The configuration of the data store can not be done like that
                if shape.data_store is not None:
                    data_source.append(shape.data_store.get_shader_data_source())
                data_source.append(heightmap.get_data_source(shape.data_store is not None))
                if biome is not None:
                    data_source.append(biome.get_data_source(shape.data_store is not None))
                appearance_source = appearance.get_data_source()
                if appearance_source is not None:
                    data_source.append(appearance_source)
                if hw_tessellation and OpenGLConfig.hardware_tessellation:
                    tessellation_control = ConstantTessellationControl()
                else:
                    tessellation_control = None
                shader = RenderingShader(
                    appearance=shader_appearance,
                    data_source=data_source,
                    lighting_model=lighting_model,
                    tessellation_control=tessellation_control,
                    vertex_control=DisplacementVertexControl(heightmap),
                    use_model_texcoord=not extra.get('create-uv', False),
                )
                surface = HeightmapFlatSurface(
                    'surface', tile_size, shape, heightmap, biome, appearance, shader, clickable=False
                )
        else:
            shader = RenderingShader(
                lighting_model=lighting_model,
                appearance=shader_appearance,
                use_model_texcoord=not extra.get('create-uv', False),
            )
            surface = MeshSurface(shape=shape, appearance=appearance, shader=shader)

        return surface


class StandaloneSurfaceYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        parent = objectsDB.get(data.parent)
        if parent is None:
            print(f"ERROR: Parent '{data.parent}' of surface '{data.name}' not found")
            return None
        surface = SurfaceYamlParser.decode_surface(data.to_dict(), {}, parent)
        parent.add_surface(surface)
        if data.active:
            parent.set_surface(surface)
        return None


ObjectYamlParser.register_object_parser('surface', StandaloneSurfaceYamlParser(), model=StandaloneSurfaceConfig)
