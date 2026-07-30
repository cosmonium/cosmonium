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


from ..entities.entity import Entity
from ..opengl import OpenGLConfig
from ..procedural.populator import CpuTerrainPopulator, GpuTerrainPopulator, RandomObjectPlacer
from ..shaders.rendering import RenderingShader
from ..shapes.mesh import MeshShape
from .appearancesparser import AppearanceYamlParser
from .schemas.populator import PopulatorConfig
from .shadersparser import VertexControlYamlParser
from .shapesparser import ShapeYamlParser
from .yamlparser import TypedYamlParser


class PlacerYamlParser(TypedYamlParser):
    @classmethod
    def decode(cls, data, default='random'):
        placer = None
        placer_type, placer_data = cls.get_type_and_data(data, default)
        if placer_type == 'random':
            placer = RandomObjectPlacer()
        else:
            print("Unknown placer", placer_type)
        return placer


class PopulatorYamlParser(TypedYamlParser):
    @classmethod
    def decode(cls, data):
        config = PopulatorConfig.model_validate(data)
        if OpenGLConfig.hardware_instancing:
            populator_type = config.type or 'gpu'
        else:
            populator_type = config.type or 'cpu'
        density = config.density / 1000000.0
        shape, extra = ShapeYamlParser.decode(config.shape)
        appearance = config.appearance
        if appearance is None:
            if isinstance(shape, MeshShape):
                appearance = 'model'
            else:
                appearance = 'textures'
        appearance = AppearanceYamlParser.decode(appearance)
        vertex_control = VertexControlYamlParser.decode(config.vertex)
        shader = RenderingShader(
            vertex_control=vertex_control,
            use_model_texcoord=not extra.get('create-uv', False),
        )
        object_template = Entity('template', shape=shape, appearance=appearance, shader=shader)
        placer = PlacerYamlParser.decode(config.placer)
        if populator_type == 'cpu':
            populator = CpuTerrainPopulator(object_template, density, config.max_instances, placer, config.min_lod)
        elif populator_type == 'gpu':
            populator = GpuTerrainPopulator(object_template, density, config.max_instances, placer, config.min_lod)
        else:
            print("Unknown populator", populator_type, data)
            populator = None
        return populator
