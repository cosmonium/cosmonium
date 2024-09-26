#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
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


from ..celestia.shaders import LunarLambertLightingModel
from ..shaders.custom import CustomShaderComponent
from ..shaders.lighting.base import ShadingLightingModel
from ..shaders.lighting.flat import FlatLightingModel
from ..shaders.lighting.lambert import LambertPhongLightingModel
from ..shaders.lighting.oren_nayar import OrenNayarPhongLightingModel
from ..shaders.lighting.pbr import PbrLightingModel

from .yamlparser import YamlModuleParser


class CustomShaderComponentYamlParser(YamlModuleParser):
    count = 0

    @classmethod
    def decode(cls, data):
        custom_id = "custom%d" % cls.count
        cls.count += 1
        custom = CustomShaderComponent(custom_id)
        for required in data.get('vertex-requires', []):
            custom.vertex_requires.add(required)
        for provides in data.get('vertex-provides', []):
            custom.vertex_provides.add(required)
        for required in data.get('fragment-requires', []):
            custom.fragment_requires.add(required)
        for required in data.get('fragment-provides', []):
            custom.fragment_provides.add(provides)

        custom.vertex_uniforms_data = [data.get('vertex-uniforms', '')]
        custom.vertex_inputs_data = [data.get('vertex-inputs', '')]
        custom.vertex_outputs_data = [data.get('vertex-outputs', '')]
        custom.vertex_extra_data = [data.get('vertex-extra', '')]
        custom.update_vertex_data = [data.get('update-vertex', '')]
        custom.update_normal_data = [data.get('update-normal', '')]
        custom.vertex_shader_data = [data.get('vertex-shader', '')]
        custom.fragment_uniforms_data = [data.get('fragment-uniforms', '')]
        custom.fragment_inputs_data = [data.get('fragment-inputs', '')]
        custom.fragment_extra_data = [data.get('fragment-extra', '')]
        custom.fragment_shader_decl_data = [data.get('fragment-shader-decl', '')]
        custom.fragment_shader_distort_coord_data = [data.get('fragment-shader-distort-coord', '')]
        custom.fragment_shader_data = [data.get('fragment-shader', '')]

        return custom


class LightingModelYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, appearance):
        (object_type, parameters) = cls.get_type_and_data(data, 'lambert-phong')
        if object_type == 'lambert-phong':
            model = ShadingLightingModel(LambertPhongLightingModel())
        elif object_type == 'oren-nayar':
            model = ShadingLightingModel(OrenNayarPhongLightingModel())
            # TODO: This should be done a better way...
            if appearance.roughness is None:
                appearance.roughness = 0.9
        elif object_type == 'lunar-lambert':
            model = LunarLambertLightingModel()
        elif object_type == 'pbr':
            model = ShadingLightingModel(PbrLightingModel())
        elif object_type == 'flat':
            model = FlatLightingModel()
        elif object_type == 'custom':
            model = CustomShaderComponentYamlParser.decode(parameters)
        else:
            print("Lighting model type", object_type, "unknown")
            model = None
        return model


class VertexControlYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        component = None
        (object_type, parameters) = cls.get_type_and_data(data, None)
        if object_type is None:
            component = None
        elif object_type == 'custom':
            component = CustomShaderComponentYamlParser.decode(parameters)
        else:
            print("Vertex control type", object_type, "unknown")
            component = None
        return component
