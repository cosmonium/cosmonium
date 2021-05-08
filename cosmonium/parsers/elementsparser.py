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

from ..bodyelements import Clouds, Ring
from ..shaders import BasicShader
from ..patchedshapes import VertexSizeLodControl, TextureLodControl, TextureOrVertexSizeLodControl
from .. import settings

from .yamlparser import YamlModuleParser
from .appearancesparser import AppearanceYamlParser
from .shapesparser import ShapeYamlParser
from .shadersparser import LightingModelYamlParser

class CloudsYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data, atmosphere):
        if data is None: return None
        height = float(data.get('height'))
        shape, extra = ShapeYamlParser.decode(data.get('shape'))
        appearance = AppearanceYamlParser.decode(data.get('appearance'))
        if shape.patchable:
            if appearance.texture is None or appearance.texture.source.procedural:
                shape.set_lod_control(VertexSizeLodControl(settings.patch_max_vertex_size,
                                                           density=settings.patch_constant_density))
            else:
                shape.set_lod_control(TextureOrVertexSizeLodControl(settings.patch_max_vertex_size,
                                                                    min_density=settings.patch_min_density,
                                                                    density=settings.patch_max_density))
        lighting_model = None
        shader = BasicShader(lighting_model=lighting_model)
        clouds = Clouds(height, appearance, shader, shape)
        if atmosphere is not None:
            atmosphere.add_shape_object(clouds)
        return clouds

class RingsYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        if data is None: return None
        inner_radius = data.get('inner-radius')
        outer_radius = data.get('outer-radius')
        lighting_model = data.get('lighting-model')
        appearance = AppearanceYamlParser.decode(data.get('appearance'), patched_shape=False)
        lighting_model = LightingModelYamlParser.decode(lighting_model, appearance)
        shader = BasicShader(lighting_model=lighting_model)
        rings = Ring(inner_radius, outer_radius, appearance, shader)
        return rings

