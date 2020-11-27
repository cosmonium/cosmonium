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
from ..shaders import BasicShader, PandaDataSource, ShaderSphereSelfShadow
from ..patchedshapes import VertexSizePatchLodControl, TextureOrVertexSizePatchLodControl
from ..heightmap import heightmapRegistry
from ..heightmapshaders import DisplacementVertexControl, HeightmapDataSource
from ..shapes import MeshShape
from ..procedural.shaders import DetailMap
from ..catalogs import objectsDB
from .. import settings

from .yamlparser import YamlModuleParser
from .objectparser import ObjectYamlParser
from .shapesparser import ShapeYamlParser
from .appearancesparser import AppearanceYamlParser
from .shadersparser import LightingModelYamlParser, ShaderAppearanceYamlParser
from .textureparser import TextureControlYamlParser
from .heightmapsparser import HeightmapYamlParser

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
        heightmap_data = data.setdefault('heightmap', previous.get('heightmap'))
        shape = data.setdefault('shape', previous.get('shape'))
        appearance = data.setdefault('appearance', previous.get('appearance'))
        lighting_model = data.setdefault('lighting-model', previous.get('lighting-model'))
        shader_appearance = data.setdefault('shader-appearance', previous.get('shader-appearance'))
        if shape is not None:
            shape, extra = ShapeYamlParser.decode(shape)
        if appearance is not None:
            appearance = AppearanceYamlParser.decode(appearance)
        if shape is None:
            recommended_shape = None
            if heightmap_data is not None:
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
        shader_appearance = ShaderAppearanceYamlParser.decode(shader_appearance, appearance)
        if shape.patchable:
            if appearance.texture is None or appearance.texture.source.procedural:
                shape.set_lod_control(VertexSizePatchLodControl(settings.patch_max_vertex_size,
                                                                density=settings.patch_constant_density))
            else:
                shape.set_lod_control(TextureOrVertexSizePatchLodControl(settings.patch_max_vertex_size,
                                                                         min_density=settings.patch_min_density,
                                                                         density=settings.patch_max_density))
        if heightmap_data is None:
            shader = BasicShader(lighting_model=lighting_model,
                                 appearance=shader_appearance,
                                 use_model_texcoord=not extra.get('create-uv', False))
            surface = FlatSurface(name, category=category, resolution=resolution, attribution=attribution,
                                  shape=shape, appearance=appearance, shader=shader)
        else:
            radius = owner.get('radius')
            if isinstance(heightmap_data, dict):
                name = data.get('name', 'heightmap')
                heightmap = HeightmapYamlParser.decode(heightmap_data, name, shape.patchable, radius)
            else:
                if shape.patchable:
                    heightmap = heightmapRegistry.get(heightmap_data + '-patched')
                else:
                    heightmap = heightmapRegistry.get(heightmap_data)
            control = data.get('control', None)
            if control is not None:
                control_parser = TextureControlYamlParser()
                (control, appearance_source) = control_parser.decode(control, appearance, heightmap, radius)
                if control is not None:
                    shader_appearance = DetailMap(control, heightmap, create_normals=True)
            else:
                shader_appearance = None
                appearance_source = PandaDataSource()
            data_source = [HeightmapDataSource(heightmap, normals=True)]
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
