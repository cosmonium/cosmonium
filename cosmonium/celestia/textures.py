from __future__ import print_function
from __future__ import absolute_import

from ..textures import VirtualTextureSource, TextureSourceFactory, AutoTextureSource
from ..dircontext import defaultDirContext

import os

class CelestiaVirtualTextureSource(VirtualTextureSource):
    def __init__(self, root, ext, size, prefix='tx_', offset=0, context=defaultDirContext):
        VirtualTextureSource.__init__(self, root, ext, size, context)
        self.prefix = prefix
        self.offset = offset

    def set_offset(self, offset):
        self.offset = offset

    def get_patch_name(self, patch, scale=1):
        sector = patch.sector
        ring = patch.ring
        if self.offset != 0:
            sector += patch.s_div // 2
            sector %= patch.s_div
        return "%s%d_%d.%s" % (self.prefix, sector * scale, ring * scale, self.ext)

    def child_texture_name(self, patch):
        return os.path.join(self.root, 'level%d' % (patch.lod + 1), self.get_patch_name(patch, 2))

    def texture_name(self, patch):
        return os.path.join(self.root, 'level%d' % patch.lod, self.get_patch_name(patch))

class CelestiaVirtualTextureSourceFactory(TextureSourceFactory):
    def create_source(self, filename, context=defaultDirContext):
        return ctx_parser.parse_file(filename, context)

#TODO: Should be done in Cosmonium main class
from . import ctx_parser
AutoTextureSource.register_source_factory(CelestiaVirtualTextureSourceFactory(), ['ctx'], 0)
