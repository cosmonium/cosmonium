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

from ..appearances import Appearance, ModelAppearance
from ..textures import AutoTextureSource, TransparentTexture, SurfaceTexture,  EmissionTexture, NormalMapTexture, SpecularMapTexture, BumpMapTexture
from ..procedural.textures import ProceduralVirtualTextureSource
from ..procedural.shadernoise import GrayTarget, AlphaTarget
from ..procedural.raymarching import RayMarchingAppearance
#TODO: Should not be here but in respective packages
from ..celestia.textures import CelestiaVirtualTextureSource
from ..spaceengine.textures import SpaceEngineVirtualTextureSource
from ..utils import TransparencyBlend

from .yamlparser import YamlModuleParser
from .noiseparser import NoiseYamlParser
from .textureparser import TextureDictionaryYamlParser

def decode_bias(data, appearance):
    appearance.shadow_normal_bias = data.get('normal-bias', appearance.shadow_normal_bias)
    appearance.shadow_slope_bias = data.get('slope-bias', appearance.shadow_slope_bias)
    appearance.shadow_depth_bias = data.get('depth-bias', appearance.shadow_depth_bias)

class TexturesAppearanceYamlParser(YamlModuleParser):
    @classmethod
    def decode_source(cls, data):
        texture_source = None
        texture_offset = None
        if isinstance(data, str):
            object_type = 'file'
            parameters = {'file': data}
        else:
            object_type = data.get('type', 'file')
            parameters = data
        if object_type == 'file':
            texture_attribution = parameters.get('attribution', None)
            texture_source = AutoTextureSource(parameters.get('file'), texture_attribution, YamlModuleParser.context)
            texture_offset = parameters.get('offset', 0)
            parameters = data
        elif object_type == 'ctx':
            root = parameters.get('root', None)
            ext = parameters.get('ext', 'dds')
            size = parameters.get('size', None)
            prefix = parameters.get('prefix', 'tx_')
            offset = parameters.get('offset', 0)
            attribution = parameters.get('attribution', None)
            texture_source = CelestiaVirtualTextureSource(root, ext, size, prefix, offset, attribution, YamlModuleParser.context)
            texture_offset = 0
        elif object_type == 'se':
            root = parameters.get('root', None)
            ext = parameters.get('ext', 'jpg')
            size = parameters.get('size', 258)
            channel = parameters.get('color', None)
            alpha_channel = parameters.get('alpha', None)
            attribution = parameters.get('attribution', None)
            texture_source = SpaceEngineVirtualTextureSource(root, ext, size, channel, alpha_channel, attribution)
            texture_offset = 0
        elif object_type == 'procedural':
            noise_parser = NoiseYamlParser()
            noise = noise_parser.decode(data.get('noise'))
            target = data.get('target', 'gray')
            if target == 'gray':
                target = GrayTarget()
            elif target == 'alpha':
                target = AlphaTarget()
            else:
                print("Unknown noise target", target)
                target = None
            size = int(data.get('size', 256))
            frequency = float(data.get('frequency', 1.0))
            scale = float(data.get('scale', 1.0))
            texture_source = ProceduralVirtualTextureSource(noise, target, size, frequency, scale)
            texture_offset = parameters.get('offset', 0)
        else:
            print("Unknown type", object_type)
        return texture_source, texture_offset

    @classmethod
    def decode(self, data):
        appearance = Appearance()
        tint = data.get('tint', None)
        if tint is not None:
            tint = LColor(*tint)
        transparency = data.get('transparency', False)
        transparency_level = data.get('transparency-level', 0.0)
        transparency_blend = data.get('transparency-blend', TransparencyBlend.TB_Alpha)
        texture = data.get('texture')
        if texture is not None:
            texture_source, texture_offset = self.decode_source(texture)
            if transparency:
                texture = TransparentTexture(texture_source, tint=tint, level=transparency_level, blend=transparency_blend)
            else:
                texture = SurfaceTexture(texture_source)
            appearance.set_texture(texture, tint=tint, transparency=transparency, transparency_level=transparency_level, transparency_blend=transparency_blend, offset=texture_offset, context=YamlModuleParser.context)
        emission_texture = data.get('night-texture')
        if emission_texture is not None:
            texture_source, texture_offset = self.decode_source(emission_texture)
            emission_texture = EmissionTexture(texture_source)
            #TODO: missing texture offset
            appearance.set_emission_texture(emission_texture, context=YamlModuleParser.context)
            nightscale = data.get('nightscale', 0.02)
            appearance.set_nightscale(nightscale)
        else:
            emission_texture = data.get('emission-texture')
            if emission_texture is not None:
                texture_source, texture_offset = self.decode_source(emission_texture)
                emission_texture = EmissionTexture(texture_source)
                #TODO: missing texture offset
                appearance.set_emission_texture(emission_texture, context=YamlModuleParser.context)
        normal_map = data.get('normalmap')
        if normal_map is not None:
            texture_source, texture_offset = self.decode_source(normal_map)
            normal_map = NormalMapTexture(texture_source)
            #TODO: missing texture offset
            appearance.set_normal_map(normal_map, context=YamlModuleParser.context)
        specular_color = data.get('specular-color')
        if specular_color is not None:
            appearance.specularColor = LColor(*specular_color)
            appearance.shininess = data.get('shininess', 1)
            specular_map = data.get('specularmap')
            if specular_map is not None:
                texture_source, texture_offset = self.decode_source(specular_map)
                specular_map = SpecularMapTexture(texture_source)
                #TODO: missing texture offset
                appearance.set_specular_map(specular_map, context=YamlModuleParser.context)
        bump_map = data.get('bumpmap')
        if bump_map is not None:
            texture_source, texture_offset = self.decode_source(bump_map)
            bump_map = BumpMapTexture(texture_source)
            bump_height = data.get('bump-height', 0)
            #TODO: missing texture offset
            appearance.set_bump_map(bump_map, bump_height, context=YamlModuleParser.context)
        diffuse_color = data.get('diffuse-color')
        if diffuse_color is not None:
            appearance.diffuseColor = LColor(*diffuse_color)
        emission_color = data.get('emission-color')
        if emission_color is not None:
            appearance.emissionColor = LColor(*emission_color)
        elif emission_texture is not None:
            appearance.emissionColor = LColor(1, 1, 1, 1)
        roughness = data.get('roughness', 0.0)
        appearance.set_roughness(roughness)
        backlit = data.get('backlit', None)
        appearance.set_backlit(backlit)
        attribution = data.get('attribution', None)
        appearance.attribution = attribution
        decode_bias(data, appearance)
        return appearance

class ModelAppearanceYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        material = data.get('material', True)
        vertex_color = data.get('vertex-color', True)
        occlusion_channel = data.get('occlusion-channel', False)
        appearance = ModelAppearance(vertex_color=vertex_color, material=material, occlusion_channel=occlusion_channel)
        decode_bias(data, appearance)
        return appearance

class RayMarchingAppeanceYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        density_coef = data.get('density-coef', 10000.0)
        density_power = data.get('density-power', 2)
        absorption_factor = data.get('absorption-factor', 0.00001)
        absorption_coef = data.get('absorption-coef', [1, 1, 1])
        mie_coef = data.get('mie-coef', 0.1)
        phase_coef = data.get('phase-coef', 0)
        source_power = data.get('source-power', 10000.0)
        emission_power = data.get('emission-power', 0.0)
        max_steps = data.get('max-steps', 16)
        return RayMarchingAppearance(density_coef, density_power,
                                     absorption_factor, absorption_coef,
                                     mie_coef, phase_coef,
                                     source_power, emission_power, max_steps)

class AppearanceYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data):
        (object_type, parameters) = self.get_type_and_data(data, 'textures', detect_trivial=False)
        if object_type == 'textures':
            appearance = TexturesAppearanceYamlParser.decode(parameters)
        elif object_type == 'model':
            appearance = ModelAppearanceYamlParser.decode(parameters)
        elif object_type == 'textures-dict':
            appearance = TextureDictionaryYamlParser.decode_textures_dictionary(parameters)
        else:
            print("Unknown appearance type '%s'" % object_type, data)
            appearance = None
        return appearance

