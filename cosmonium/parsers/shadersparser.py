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

from panda3d.core import LColor

from ..shaders import FlatLightingModel, LambertPhongLightingModel, OrenNayarPhongLightingModel, CustomShaderComponent
from ..pbr import PbrLightingModel
from ..celestia.shaders import LunarLambertLightingModel

from .yamlparser import YamlModuleParser

class CustomShaderComponentYamlParser(YamlModuleParser):
    count = 0
    @classmethod
    def decode(cls, data):
        custom_id = "custom%d" % cls.count
        cls.count += 1
        custom = CustomShaderComponent(custom_id)
        custom.use_vertex = data.get('use-vertex', False)
        custom.use_vertex_frag = data.get('use-vertex-frag', False)
        custom.model_vertex = data.get('model-vertex', False)
        custom.world_vertex = data.get('world-vertex', False)
        custom.use_normal = data.get('use-normal', False)
        custom.model_normal = data.get('model-normal', False)
        custom.world_normal = data.get('world-normal', False)
        custom.use_tangent = data.get('use-tangent', False)
        if data.get('update-vertex') is not None:
            custom.has_vertex = True
        if data.get('update-normal') is not None:
            custom.has_normal = True

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
            model = LambertPhongLightingModel()
        elif object_type == 'oren-nayar':
            model = OrenNayarPhongLightingModel()
            #TODO: This should be done a better way...
            if appearance.roughness is None:
                appearance.roughness = 0.9
        elif object_type == 'lunar-lambert':
            model = LunarLambertLightingModel()
        elif object_type == 'pbr':
            model = PbrLightingModel()
        elif object_type == 'flat':
            model = FlatLightingModel()
            #TODO: This should be done a better way...
            if appearance.emissionColor is None:
                appearance.emissionColor = LColor(1, 1, 1, 1)
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
        if object_type == None:
            component = None
        elif object_type == 'custom':
            component = CustomShaderComponentYamlParser.decode(parameters)
        else:
            print("Vertex control type", object_type, "unknown")
            component = None
        return component
