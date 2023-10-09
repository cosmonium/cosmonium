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


from ..shaders.rendering import RenderingShader
from ..shapes.mesh import MeshShape
from ..shapes.shape_object import ShapeObject

from .appearancesparser import AppearanceYamlParser
from .shadersparser import LightingModelYamlParser
from .shapesparser import ShapeYamlParser
from .yamlparser import YamlModuleParser


class EntityYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        if data is None: return None
        name = data.get('name')
        shape, extra = ShapeYamlParser.decode(data.get('shape'))
        appearance_data = data.get('appearance')
        if appearance_data is None:
            if isinstance(shape, MeshShape):
                appearance_data = 'model'
            else:
                appearance_data = 'textures'
        appearance = AppearanceYamlParser.decode(appearance_data)
        lighting_model = LightingModelYamlParser.decode(data.get('lighting-model'), appearance)
        shader = RenderingShader(lighting_model=lighting_model)
        entity = ShapeObject(name, shape, appearance, shader)
        return entity
