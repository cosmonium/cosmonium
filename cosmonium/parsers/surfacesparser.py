#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2023 Laurent Deru.
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


from ..components.elements.surfaces import EllipsoidFlatSurface, MeshSurface, HeightmapSurface
from ..components.elements.surface_categories import surfaceCategoryDB, SurfaceCategory
from ..shaders.rendering import RenderingShader
from ..shaders.vertex_control.displacement import DisplacementVertexControl
from ..patchedshapes import VertexSizeLodControl, TextureOrVertexSizeLodControl
from ..heightmap import heightmapRegistry
from ..shapes.mesh import MeshShape
from ..catalogs import objectsDB
from .. import settings

from .yamlparser import YamlModuleParser
from .objectparser import ObjectYamlParser
from .shapesparser import ShapeYamlParser
from .appearancesparser import AppearanceYamlParser
from .shadersparser import LightingModelYamlParser
from .heightmapsparser import HeightmapYamlParser
from .utilsparser import get_radius_scale

class SurfaceYamlParser(YamlModuleParser):
    @classmethod
    def decode_surface(self, data, previous, owner):
        name = data.get('name', None)
        category_name = data.get('category', 'visible')
        category = surfaceCategoryDB.get(category_name)
        if category is None:
            print("Category '%s' unknown" % category_name)
            category = SurfaceCategory(category_name)
            surfaceCategoryDB.add(category)
        resolution = data.get('resolution', None)
        attribution = data.get('attribution', data.get('source'))
        radius, ellipticity, scale = get_radius_scale(data, owner)
        #The next parameters are using set_default in order to propagate
        #their manual configuration to the next surface, if any.
        heightmap_data = data.setdefault('heightmap', previous.get('heightmap'))
        shape = data.setdefault('shape', previous.get('shape'))
        appearance = data.setdefault('appearance', previous.get('appearance'))
        lighting_model = data.setdefault('lighting-model', previous.get('lighting-model'))
        if shape is None and heightmap_data is not None:
            shape = 'sqrt-sphere'
        if shape is not None:
            shape, extra = ShapeYamlParser.decode(shape, radius=radius)
        if heightmap_data is not None:
            if isinstance(heightmap_data, dict):
                name = data.get('name', 'heightmap')
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
                    shape.set_lod_control(VertexSizeLodControl(settings.patch_max_vertex_size,
                                                               density=settings.patch_constant_density))
                else:
                    shape.set_lod_control(TextureOrVertexSizeLodControl(settings.patch_max_vertex_size,
                                                                        min_density=settings.patch_min_density,
                                                                        density=settings.patch_max_density))
            if heightmap is None:
                shader = RenderingShader(lighting_model=lighting_model,
                                     appearance=shader_appearance,
                                     use_model_texcoord=not extra.get('create-uv', False))
                surface = EllipsoidFlatSurface(name, category=category, resolution=resolution, attribution=attribution,
                                      radius=radius, oblateness=ellipticity, scale=scale,
                                      shape=shape, appearance=appearance, shader=shader)
            else:
                data_source = []
                #TODO: The configuration of the data store can not be done like that
                if shape.data_store is not None:
                    data_source.append(shape.data_store.get_shader_data_source())
                data_source.append(heightmap.get_data_source(shape.data_store is not None))
                appearance_source = appearance.get_data_source()
                if appearance_source is not None:
                    data_source.append(appearance_source)
                shader = RenderingShader(vertex_control=DisplacementVertexControl(heightmap),
                                     data_source=data_source,
                                     appearance=shader_appearance,
                                     lighting_model=lighting_model,
                                     use_model_texcoord=not extra.get('create-uv', False))
                surface = HeightmapSurface(name,
                                           #category=category, resolution=resolution, source=source,
                                           radius=radius, oblateness=ellipticity, scale=scale,
                                           height_scale=radius,
                                           shape=shape, heightmap=heightmap, biome=None, appearance=appearance, shader=shader)
        else:
                shader = RenderingShader(lighting_model=lighting_model,
                                     appearance=shader_appearance,
                                     use_model_texcoord=not extra.get('create-uv', False))
                surface = MeshSurface(name, category=category, resolution=resolution, attribution=attribution,
                                      shape=shape, appearance=appearance, shader=shader)
        return surface

    @classmethod
    def decode(self, data, owner):
        surfaces = []
        #TODO: Should do surface element cloning instead of reparsing
        previous = {}
        for entry in data:
            surface = self.decode_surface(entry, previous, owner)
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
        surface = SurfaceYamlParser.decode_surface(data, {}, parent)
        parent.add_surface(surface)
        if active:
            parent.set_surface(surface)
        return None

ObjectYamlParser.register_object_parser('surface', StandaloneSurfaceYamlParser())
