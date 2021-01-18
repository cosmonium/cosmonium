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

from ..procedural.appearances import TexturesDictionary, TextureTilingMode

from ..textures import AutoTextureSource
from ..textures import TransparentTexture, SurfaceTexture,  EmissionTexture, NormalMapTexture, SpecularMapTexture, BumpMapTexture, OcclusionMapTexture
from ..appearances import TexturesBlock

from .yamlparser import YamlModuleParser

class TextureTilingYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        (object_type, object_data) = cls.get_type_and_data(data, 'default')
        if object_type == 'default':
            return TextureTilingMode.F_none
        elif object_type == 'hash':
            return TextureTilingMode.F_hash
        else:
            print("Unknown tiling type '%s'" % object_type)
            return TextureTilingMode.F_none

class TextureDictionaryYamlParser(YamlModuleParser):
    @classmethod
    def decode_texture_albedo(self, data, srgb):
        if data is not None:
            if isinstance(data, str):
                texture_source = AutoTextureSource(data, context=YamlModuleParser.context)
                data = {}
            else:
                texture_source = AutoTextureSource(data.get('file'), context=YamlModuleParser.context)
            srgb = data.get('srgb', srgb)
            albedo = SurfaceTexture(texture_source, srgb)
        else:
            albedo = None
        return albedo

    @classmethod
    def decode_texture_normal(self, data):
        if data is not None:
            if isinstance(data, str):
                texture_source = AutoTextureSource(data, context=YamlModuleParser.context)
                data = {}
            else:
                texture_source = AutoTextureSource(data.get('file'), context=YamlModuleParser.context)
            normal = NormalMapTexture(texture_source)
        else:
            normal = None
        return normal

    @classmethod
    def decode_texture_occlusion(self, data):
        if data is not None:
            if isinstance(data, str):
                texture_source = AutoTextureSource(data, context=YamlModuleParser.context)
                data = {}
            else:
                texture_source = AutoTextureSource(data.get('file'), context=YamlModuleParser.context)
            occlusion = OcclusionMapTexture(texture_source)
        else:
            occlusion = None
        return occlusion

    @classmethod
    def decode_textures_dictionary_entry(self, data, srgb):
        entry = TexturesBlock()
        if isinstance(data, str):
            albedo = self.decode_texture_albedo(data, srgb)
            entry.set_albedo(albedo)
        else:
            albedo = self.decode_texture_albedo(data.get('albedo'), srgb)
            if albedo is not None:
                entry.set_albedo(albedo)
            normal = self.decode_texture_normal(data.get('normal'))
            if normal is not None:
                entry.set_normal(normal)
            occlusion = self.decode_texture_occlusion(data.get('occlusion'))
            if occlusion is not None:
                entry.set_occlusion(occlusion)
        return entry

    @classmethod
    def decode_textures_dictionary(cls, data):
        entries = {}
        srgb = data.get('srgb')
        for (name, entry) in data.get('entries', {}).items():
            entries[name] = cls.decode_textures_dictionary_entry(entry, srgb)
        scale = data.get('scale')
        tiling = TextureTilingYamlParser.decode(data.get('tiling'))
        return TexturesDictionary(entries, scale, tiling, context=YamlModuleParser.context)

    @classmethod
    def decode(cls, data):
        entry_type = list(data)[0]
        entry = data[entry_type]
        if entry_type == 'textures':
            return cls.decode_textures_dictionary(entry)
        else:
            return None
