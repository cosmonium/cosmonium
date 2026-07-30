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


# TODO: Should not be here but in respective packages
from ..celestia.textures import CelestiaVirtualTextureSource
from ..procedural.shadernoise import AlphaTarget, GrayTarget
from ..procedural.textures import (
    NoiseTextureGenerator,
    PatchedProceduralVirtualTextureSource,
    ProceduralVirtualTextureSource,
)
from ..spaceengine.textures import SpaceEngineVirtualTextureSource
from ..textures import AutoTextureSource
from .noiseparser import NoiseYamlParser
from .schemas.texturesource import (
    CelestiaVirtualTextureSourceConfig,
    ProceduralTextureSourceConfig,
    ReferenceTextureSourceConfig,
    SpaceEngineVirtualTextureSourceConfig,
    TextureFileSourceConfig,
)
from .yamlparser import TypedYamlParser, YamlModuleParser


class ReferenceTextureSourceYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, patched_shape=True):
        # TODO: This is a hack, a proper reference object should be used
        try:
            texture_source = TextureSourceYamlParser.tex_references[data.ref]
            texture_offset = 0
            return texture_source, texture_offset
        except KeyError:
            print("Reference '%s' not found" % data.ref)
            return None, None


class TextureFileSourceYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, patched_shape=True):
        texture_source = AutoTextureSource(data.file, YamlModuleParser.context)
        if data.attribution:
            texture_source.set_attribution(data.attribution)
        texture_offset = data.offset
        return texture_source, texture_offset


# TODO: Should not be here but in its own package
class CelestiaVirtualTextureSourceYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, patched_shape=True):
        texture_source = CelestiaVirtualTextureSource(
            data.root, data.ext, data.size, data.prefix, data.offset, YamlModuleParser.context
        )
        if data.attribution:
            texture_source.set_attribution(data.attribution)
        texture_offset = 0
        return texture_source, texture_offset


# TODO: Should not be here but in its own package
class SpaceEngineVirtualTextureSourceYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, patched_shape=True):
        texture_source = SpaceEngineVirtualTextureSource(
            data.root, data.ext, data.size, data.color, data.alpha, YamlModuleParser.context
        )
        if data.attribution:
            texture_source.set_attribution(data.attribution)
        texture_offset = 0
        return texture_source, texture_offset


class ProceduralTextureSourceYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data, patched_shape=True):
        noise_parser = NoiseYamlParser()
        func = data.func
        if func is None:
            func = data.noise
            print("Warning: 'noise' entry is deprecated, use 'func' instead")
        func = noise_parser.decode(func)
        has_alpha = False
        use_srgb = False
        if data.target == 'gray':
            target = GrayTarget()
        elif data.target == 'alpha':
            target = AlphaTarget()
            has_alpha = True
        else:
            print("Unknown noise target", data.target)
            target = None
        tex_generator = NoiseTextureGenerator(data.size, func, target, alpha=has_alpha, srgb=use_srgb)
        if patched_shape:
            texture_source = PatchedProceduralVirtualTextureSource(tex_generator, data.size)
        else:
            texture_source = ProceduralVirtualTextureSource(tex_generator, data.size)
        texture_offset = 0
        return texture_source, texture_offset


class TextureSourceYamlParser(TypedYamlParser):
    default_type = 'file'
    tex_references = {}

    @classmethod
    def canonize_data(cls, data):
        if isinstance(data, str):
            if data.startswith('ref:'):
                parameters = {'type': 'ref', 'ref': data.split(':', 2)[1]}
            else:
                parameters = {'type': 'file', 'file': data}
        else:
            parameters = data
        return parameters

    @classmethod
    def decode_object(cls, data, **extra):
        # TODO: The named references should be handled in a more robust way,
        # with a proper reference object and resolution mechanism
        data = cls.canonize_data(data)
        object_type, parameters = cls.get_type_and_data(data, cls.default_type, detect_trivial=cls.detect_trivial)
        if object_type in cls.parsers:
            parser = cls.parsers[object_type]
            # Validate parameters if model is registered
            validated_parameters = cls.validate_and_decode(object_type, parameters)
            texture_source, texture_offset = parser.decode(validated_parameters, **extra)
            if hasattr(validated_parameters, 'name'):
                name = validated_parameters.name
                if texture_source is not None and name is not None:
                    cls.tex_references[name] = texture_source
            result = (texture_source, texture_offset)
        else:
            print("Unknown type '%s'" % object_type)
            result = (None, None)
        return result


def register_texture_source_parsers():
    TextureSourceYamlParser.register_parser('ref', ReferenceTextureSourceYamlParser(), ReferenceTextureSourceConfig)
    TextureSourceYamlParser.register_parser('file', TextureFileSourceYamlParser(), TextureFileSourceConfig)
    TextureSourceYamlParser.register_parser(
        'ctx', CelestiaVirtualTextureSourceYamlParser(), CelestiaVirtualTextureSourceConfig
    )
    TextureSourceYamlParser.register_parser(
        'se', SpaceEngineVirtualTextureSourceYamlParser(), SpaceEngineVirtualTextureSourceConfig
    )
    TextureSourceYamlParser.register_parser(
        'procedural', ProceduralTextureSourceYamlParser(), ProceduralTextureSourceConfig
    )
