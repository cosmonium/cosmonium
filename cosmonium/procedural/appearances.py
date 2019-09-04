from __future__ import print_function
from __future__ import absolute_import

from ..appearances import AppearanceBase
from ..textures import TextureBase
from ..procedural.detailtextures import DetailTexture
from cosmonium.dircontext import defaultDirContext

class TextureTilingMode(object):
    F_none = 0
    F_hash = 1

class TexturesDictionary(AppearanceBase):
    def __init__(self, textures, scale_factor=(1.0, 1.0), tiling=TextureTilingMode.F_none, shadow=None, texture_class=DetailTexture, context=defaultDirContext):
        AppearanceBase.__init__(self)
        self.textures = textures
        self.scale_factor = scale_factor
        self.tiling = tiling
        self.shadow = shadow
        for (name, texture) in self.textures.items():
            if texture is not None and not isinstance(texture, TextureBase):
                self.textures[name] = texture_class(texture, context)

    def set_shadow(self, shadow):
        self.shadow = shadow

    def apply(self, shape, owner, direct=True):
        for (name, texture) in self.textures.items():
            texture.load(shape)
            texture.apply(shape, "tex_" + name)

class ProceduralAppearance(AppearanceBase):
    def __init__(self,
                 scale_factor = (1, 1),
                 shadow=None):
        AppearanceBase.__init__(self)
        self.shadow = shadow
        self.scale_factor = scale_factor

    def set_shadow(self, shadow):
        self.shadow = shadow
