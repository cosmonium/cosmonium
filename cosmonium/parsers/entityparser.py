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
from ..shaders.rendering import RenderingShader
from ..shapes.mesh import MeshShape
from .appearancesparser import AppearanceYamlParser
from .schemas.entity import EntityConfig
from .shadersparser import LightingModelYamlParser
from .shapesparser import ShapeYamlParser
from .yamlparser import YamlModuleParser


class EntityYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        config = EntityConfig.model_validate(data)
        # TODO: Disabled entity is treated as non-existent, so we return None instead of an entity object
        # We should return an entity object with a disabled flag instead of None
        if config.disabled:
            return None
        shape, extra = ShapeYamlParser.decode(config.shape)
        appearance_data = config.appearance
        if appearance_data is None:
            if isinstance(shape, MeshShape):
                appearance_data = 'model'
            else:
                appearance_data = 'textures'
        appearance = AppearanceYamlParser.decode(appearance_data)
        lighting_model = LightingModelYamlParser.decode(config.lighting_model, appearance)
        shader = RenderingShader(lighting_model=lighting_model)
        entity = Entity(config.name, shape, appearance, shader)
        entity.physics = config.physics
        return entity
