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


from panda3d.core import LColor

from ..appearances import Appearance, ModelAppearance
from ..procedural.appearances import ProceduralAppearance
from ..procedural.textures import DetailMapTextureGenerator, PatchedProceduralVirtualTextureSource
from ..textures import (
    BumpMapTexture,
    EmissionTexture,
    NormalMapTexture,
    SpecularMapTexture,
    SurfaceTexture,
    TransparentTexture,
)
from ..utils import TransparencyBlend
from .schemas.appearance import (
    DeferredProceduralAppearanceConfig,
    ModelAppearanceConfig,
    ProceduralAppearanceConfig,
    TexturesAppearanceConfig,
)
from .texturecontrolparser import TextureControlYamlParser
from .textureparser import TextureDictionaryYamlParser
from .texturesourceparser import TextureSourceYamlParser
from .yamlparser import TypedYamlParser, YamlModuleParser


def decode_bias(data, appearance):
    if data.normal_bias is not None:
        appearance.shadow_normal_bias = data.normal_bias
    if data.slope_bias is not None:
        appearance.shadow_slope_bias = data.slope_bias
    if data.depth_bias is not None:
        appearance.shadow_depth_bias = data.depth_bias


class TexturesAppearanceYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, heightmap, radius, patched_shape):
        source_parser = TextureSourceYamlParser()
        appearance = Appearance()
        if data.tint is not None:
            tint = data.tint
        else:
            tint = None
        transparency = data.transparency
        transparency_level = data.transparency_level
        transparency_blend = data.transparency_blend
        if transparency_blend is None:
            transparency_blend = TransparencyBlend.TB_Alpha
        if data.texture is not None:
            texture_source, texture_offset = source_parser.decode(data.texture, patched_shape=patched_shape)
            if transparency:
                texture = TransparentTexture(
                    texture_source, tint=tint, level=transparency_level, blend=transparency_blend
                )
            else:
                texture = SurfaceTexture(texture_source)
            if texture_offset is not None:
                texture.offset = texture_offset
            appearance.set_texture(
                texture,
                tint=tint,
                transparency=transparency,
                transparency_level=transparency_level,
                transparency_blend=transparency_blend,
            )
        if data.night_texture is not None:
            texture_source, texture_offset = source_parser.decode(data.night_texture, patched_shape=patched_shape)
            emission_texture = EmissionTexture(texture_source)
            # TODO: missing texture offset
            appearance.set_emission_texture(emission_texture, context=YamlModuleParser.context)
            appearance.set_nightscale(data.nightscale)
        elif data.emission_texture is not None:
            texture_source, texture_offset = source_parser.decode(data.emission_texture, patched_shape=patched_shape)
            emission_texture = EmissionTexture(texture_source)
            # TODO: missing texture offset
            appearance.set_emission_texture(emission_texture, context=YamlModuleParser.context)
        if data.normalmap is not None:
            texture_source, texture_offset = source_parser.decode(data.normalmap, patched_shape=patched_shape)
            normal_map = NormalMapTexture(texture_source)
            # TODO: missing texture offset
            appearance.set_normal_map(normal_map, context=YamlModuleParser.context)
        if data.specular_color is not None:
            appearance.specularColor = data.specular_color
            appearance.shininess = data.shininess
            if data.specularmap is not None:
                texture_source, texture_offset = source_parser.decode(data.specularmap, patched_shape=patched_shape)
                specular_map = SpecularMapTexture(texture_source)
                # TODO: missing texture offset
                appearance.set_specular_map(specular_map, context=YamlModuleParser.context)
        if data.bumpmap is not None:
            texture_source, texture_offset = source_parser.decode(data.bumpmap, patched_shape=patched_shape)
            bump_map = BumpMapTexture(texture_source)
            # TODO: missing texture offset
            appearance.set_bump_map(bump_map, data.bump_height, context=YamlModuleParser.context)
        if data.diffuse_color is not None:
            appearance.diffuseColor = data.diffuse_color
        if data.emission_color is not None:
            appearance.emissionColor = data.emission_color
        elif data.night_texture is not None or data.emission_texture is not None:
            appearance.emissionColor = LColor(1, 1, 1, 1)
        appearance.set_roughness(data.roughness)
        appearance.set_backlit(data.backlit)
        appearance.attribution = data.attribution
        decode_bias(data, appearance)
        return appearance


class ModelAppearanceYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, heightmap, radius, patched_shape):
        appearance = ModelAppearance(
            vertex_color=data.vertex_color, material=data.material, occlusion_channel=data.occlusion_channel
        )
        decode_bias(data, appearance)
        return appearance


class ProceduralAppearanceYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, heightmap, radius, patched_shape):
        control_parser = TextureControlYamlParser()
        textures_source = TextureDictionaryYamlParser.decode(data.textures)
        texture_control = control_parser.decode(data.control, heightmap, radius)
        appearance = ProceduralAppearance(texture_control, textures_source, heightmap)
        return appearance


class DeferredProceduralAppearanceYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, heightmap, radius, patched_shape):
        control_parser = TextureControlYamlParser()
        textures_source = TextureDictionaryYamlParser.decode(data.textures)
        texture_control = control_parser.decode(data.control, heightmap, radius)
        tex_generator = DetailMapTextureGenerator(data.size, heightmap, texture_control, textures_source)
        texture_source = PatchedProceduralVirtualTextureSource(tex_generator, data.size)
        texture_source.procedural = False
        texture = SurfaceTexture(texture_source)
        appearance = Appearance()
        appearance.set_texture(texture, None, False, 0.0, TransparencyBlend.TB_None, 0)
        return appearance


class AppearanceYamlParser(TypedYamlParser):
    @classmethod
    def decode(cls, data, heightmap=None, radius=None, patched_shape=True):
        (object_type, parameters) = cls.get_type_and_data(data, 'textures', detect_trivial=False)
        validated_data = cls.validate_and_decode(object_type, parameters)
        # Get registered parser if exists
        if object_type in cls.parsers:
            parser = cls.parsers[object_type]
            return parser.decode(validated_data, heightmap, radius, patched_shape)
        else:
            print("Unknown appearance type '%s'" % object_type, data)
            return None


def register_appearance_parsers():
    AppearanceYamlParser.register_parser('textures', TexturesAppearanceYamlParser, TexturesAppearanceConfig)
    AppearanceYamlParser.register_parser('model', ModelAppearanceYamlParser, ModelAppearanceConfig)
    AppearanceYamlParser.register_parser('procedural', ProceduralAppearanceYamlParser, ProceduralAppearanceConfig)
    AppearanceYamlParser.register_parser(
        'deferred-procedural', DeferredProceduralAppearanceYamlParser, DeferredProceduralAppearanceConfig
    )
