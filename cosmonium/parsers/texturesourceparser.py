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


from ..textures import AutoTextureSource
from ..procedural.textures import ProceduralVirtualTextureSource
from ..procedural.shadernoise import GrayTarget, AlphaTarget
#TODO: Should not be here but in respective packages
from ..celestia.textures import CelestiaVirtualTextureSource
from ..spaceengine.textures import SpaceEngineVirtualTextureSource

from .yamlparser import YamlModuleParser
from .noiseparser import NoiseYamlParser

class ReferenceTextureSourceYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        #TODO: This is a hack, a proper reference object should be used
        ref_name = data.get('ref')
        texture_source = TextureSourceYamlParser.tex_references.get(ref_name)
        texture_offset = 0
        return texture_source, texture_offset

class TextureFileSourceYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        texture_attribution = data.get('attribution', None)
        texture_source = AutoTextureSource(data.get('file'), texture_attribution, YamlModuleParser.context)
        texture_offset = data.get('offset', 0)
        return texture_source, texture_offset

#TODO: Should not be here but in its own package
class CelestiaVirtualTextureSourceYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        root = data.get('root', None)
        ext = data.get('ext', 'dds')
        size = data.get('size', None)
        prefix = data.get('prefix', 'tx_')
        offset = data.get('offset', 0)
        attribution = data.get('attribution', None)
        texture_source = CelestiaVirtualTextureSource(root, ext, size, prefix, offset, attribution, YamlModuleParser.context)
        texture_offset = 0
        return texture_source, texture_offset

#TODO: Should not be here but in its own package
class SpaceEngineVirtualTextureSourceYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        root = data.get('root', None)
        ext = data.get('ext', 'jpg')
        size = data.get('size', 258)
        channel = data.get('color', None)
        alpha_channel = data.get('alpha', None)
        attribution = data.get('attribution', None)
        texture_source = SpaceEngineVirtualTextureSource(root, ext, size, channel, alpha_channel, attribution, YamlModuleParser.context)
        texture_offset = 0
        return texture_source, texture_offset

class ProceduralTextureSourceYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        noise_parser = NoiseYamlParser()
        func = data.get('func')
        if func is None:
            func = data.get('noise')
            print("Warning: 'noise' entry is deprecated, use 'func' instead'")
        func = noise_parser.decode(func)
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
        texture_source = ProceduralVirtualTextureSource(func, target, size)
        texture_offset = data.get('offset', 0)
        return texture_source, texture_offset

class TextureSourceYamlParser(YamlModuleParser):
    tex_references = {}
    parsers = {}

    @classmethod
    def register_parser(cls, name, parser):
        cls.parsers[name] = parser

    @classmethod
    def canonize_data(cls, data):
        if isinstance(data, str):
            if data.startswith('ref:'):
                parameters = {'type': 'ref',
                              'ref': data.split(':', 2)[1]}
            else:
                parameters = {'type': 'file',
                              'file': data}
        else:
            parameters = data
        return parameters

    @classmethod
    def decode(cls, data):
        data = cls.canonize_data(data)
        object_type = data.get('type', 'file')
        if object_type in cls.parsers:
            texture_source, texture_offset = cls.parsers[object_type].decode(data)
            name = data.get('name')
            if texture_source is not None and name is not None:
                cls.tex_references[name] = texture_source
            result = (texture_source, texture_offset)
        else:
            print("Unknown object type", object_type)
            result = (None, None)
        return result

TextureSourceYamlParser.register_parser('ref', ReferenceTextureSourceYamlParser())
TextureSourceYamlParser.register_parser('file', TextureFileSourceYamlParser())
TextureSourceYamlParser.register_parser('ctx', CelestiaVirtualTextureSourceYamlParser())
TextureSourceYamlParser.register_parser('se', SpaceEngineVirtualTextureSourceYamlParser())
TextureSourceYamlParser.register_parser('procedural', ProceduralTextureSourceYamlParser())
