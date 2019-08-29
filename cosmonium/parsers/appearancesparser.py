from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import LColor

from ..shapes import MeshShape
from ..appearances import Appearance, ModelAppearance
from ..textures import AutoTextureSource, TransparentTexture, SurfaceTexture
from ..procedural.textures import ProceduralVirtualTextureSource
from ..utils import TransparencyBlend

from .yamlparser import YamlModuleParser
from .noiseparser import NoiseYamlParser
from .textureparser import TextureDictionaryYamlParser
from cosmonium.utils import TransparencyBlend

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
        elif object_type == 'procedural':
            noise_parser = NoiseYamlParser()
            noise = noise_parser.decode(data.get('noise'))
            size = int(data.get('size', 256))
            texture_source = ProceduralVirtualTextureSource(noise, size)
            texture_offset = parameters.get('offset', 0)
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
        appearance.set_night_texture(data.get('night-texture'), context=YamlModuleParser.context)
        appearance.set_normal_map(data.get('normalmap'), context=YamlModuleParser.context)
        specular_color = data.get('specular-color')
        if specular_color is not None:
            appearance.specularColor = LColor(*specular_color)
            appearance.shininess = data.get('shininess', 1)
            appearance.set_specular_map(data.get('specularmap'), context=YamlModuleParser.context)
        appearance.set_bump_map(data.get('bumpmap'), data.get('bump-height', 0), context=YamlModuleParser.context)
        diffuse_color = data.get('diffuse-color')
        if diffuse_color is not None:
            appearance.diffuseColor = LColor(*diffuse_color)
        roughness = data.get('roughness', 0.0)
        appearance.set_roughness(roughness)
        backlit = data.get('backlit', 0.0)
        appearance.set_backlit(backlit)
        attribution = data.get('attribution', None)
        appearance.attribution = attribution
        return appearance

class AppearanceYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data, shape):
        if data is None:
            if isinstance(shape, MeshShape):
                return ModelAppearance()
            else:
                return Appearance()
        if isinstance(data, str):
            object_type = data
            parameters = {}
        else:
            object_type = data.get('type', 'textures')
            parameters = data
        if object_type == 'textures':
            appearance = TexturesAppearanceYamlParser.decode(parameters)
        elif object_type == 'textures-dict':
            appearance = TextureDictionaryYamlParser.decode_textures_dictionary(parameters)
        else:
            print("Unknown appearance type '%s'" % object_type, data)
            appearance = None
        return appearance

