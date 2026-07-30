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


from ..celestia.shaders import LunarLambertLightingModel
from ..shaders.custom import CustomShaderComponent
from ..shaders.lighting.base import ShadingLightingModel
from ..shaders.lighting.flat import FlatLightingModel
from ..shaders.lighting.lambert import LambertPhongLightingModel
from ..shaders.lighting.oren_nayar import OrenNayarPhongLightingModel
from ..shaders.lighting.pbr import PbrLightingModel
from .schemas.shader import CustomShaderComponentConfig
from .yamlparser import TypedYamlParser, YamlModuleParser


class CustomShaderComponentYamlParser(YamlModuleParser):
    count = 0

    @classmethod
    def decode(cls, data):
        config = CustomShaderComponentConfig.model_validate(data)
        custom_id = "custom%d" % cls.count
        cls.count += 1
        custom = CustomShaderComponent(custom_id)
        for required in config.vertex_requires:
            custom.vertex_requires.add(required)
        for provide in config.vertex_provides:
            custom.vertex_provides.add(provide)
        for required in config.fragment_requires:
            custom.fragment_requires.add(required)
        for provide in config.fragment_provides:
            custom.fragment_provides.add(provide)

        custom.vertex_uniforms_data = [config.vertex_uniforms]
        custom.vertex_inputs_data = [config.vertex_inputs]
        custom.vertex_outputs_data = [config.vertex_outputs]
        custom.vertex_extra_data = [config.vertex_extra]
        custom.update_vertex_data = [config.update_vertex]
        custom.update_normal_data = [config.update_normal]
        custom.vertex_shader_data = [config.vertex_shader]
        custom.fragment_uniforms_data = [config.fragment_uniforms]
        custom.fragment_inputs_data = [config.fragment_inputs]
        custom.fragment_extra_data = [config.fragment_extra]
        custom.fragment_shader_decl_data = [config.fragment_shader_decl]
        custom.fragment_shader_distort_coord_data = [config.fragment_shader_distort_coord]
        custom.fragment_shader_data = [config.fragment_shader]

        return custom


class LightingModelYamlParser(TypedYamlParser):
    @classmethod
    def decode(cls, data, appearance):
        object_type, parameters = cls.get_type_and_data(data, 'lambert-phong')
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


class VertexControlYamlParser(TypedYamlParser):
    @classmethod
    def decode(cls, data):
        component = None
        object_type, parameters = cls.get_type_and_data(data, None)
        if object_type is None:
            component = None
        elif object_type == 'custom':
            component = CustomShaderComponentYamlParser.decode(parameters)
        else:
            print("Vertex control type", object_type, "unknown")
            component = None
        return component
