#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2025 Laurent Deru.
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
from .actorshapeparser import ActorShapeYamlParser
from .appearancesparser import AppearanceYamlParser
from .schemas.actor import ActorObjectConfig
from .shadersparser import LightingModelYamlParser
from .yamlparser import YamlModuleParser


class ActorObjectYamlParser(YamlModuleParser):

    @classmethod
    def decode(cls, data):
        config = ActorObjectConfig.model_validate(data)
        shape, extra = ActorShapeYamlParser.decode(config.shape)
        appearance = config.appearance
        if appearance is None:
            if isinstance(shape, MeshShape):
                appearance = 'model'
            else:
                appearance = 'textures'
        appearance = AppearanceYamlParser.decode(appearance)
        lighting_model = LightingModelYamlParser.decode(config.lighting_model, appearance)
        shader = RenderingShader(lighting_model=lighting_model, use_model_texcoord=not extra.get('create-uv', False))
        actor_object = Entity(config.name, shape=shape, appearance=appearance, shader=shader)
        return actor_object
