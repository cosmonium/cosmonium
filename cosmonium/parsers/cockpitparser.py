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

from ..cockpit import Cockpit
from ..shaders import BasicShader
from ..shapes import MeshShape

from .yamlparser import YamlModuleParser
from .objectparser import ObjectYamlParser
from .shapesparser import ShapeYamlParser
from .appearancesparser import AppearanceYamlParser
from .shadersparser import LightingModelYamlParser

class CockpitYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        name = data.get('name')
        shape = data.get('shape')
        appearance = data.get('appearance')
        lighting_model = data.get('lighting-model')
        shape, extra = ShapeYamlParser.decode(shape)
        if appearance is None:
            if isinstance(shape, MeshShape):
                appearance = 'model'
            else:
                appearance = 'textures'
        appearance = AppearanceYamlParser.decode(appearance)
        lighting_model = LightingModelYamlParser.decode(lighting_model, appearance)
        shader = BasicShader(lighting_model=lighting_model,
                             use_model_texcoord=not extra.get('create-uv', False))
        cockpit = Cockpit(name, shape=shape, appearance=appearance, shader=shader)
        self.app.add_cockpit(cockpit)

ObjectYamlParser.register_object_parser('cockpit', CockpitYamlParser())
