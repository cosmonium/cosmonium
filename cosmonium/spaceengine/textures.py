from __future__ import print_function
from __future__ import absolute_import

from ..textures import VirtualTextureSource, TextureSourceFactory, AutoTextureSource
from ..dircontext import defaultDirContext

import os

class SpaceEngineVirtualTextureSource(VirtualTextureSource):
    face_str = [
                #SE Axis :
                # X : Right -> X
                # Y : Up -> Z
                # Z : Forward -> -Y
                'pos_x',
                'neg_x',
                'pos_z',
                'neg_z',
                'pos_y',
                'neg_y',
                ]

    def __init__(self, root, ext, size, channel=None):
        VirtualTextureSource.__init__(self, root, ext, size)
        if channel is None:
            channel = ''
        else:
            channel = '_' + channel
        self.channel = channel

    def child_texture_name(self, patch):
        dir_name = self.face_str[patch.face]
        return self.root + '/' + dir_name + "/%d_%d_%d%s.%s" % (patch.lod + 1, patch.y * 2, patch.x * 2, self.channel, self.ext)

    def texture_name(self, patch):
        dir_name = self.face_str[patch.face]
        return self.root + '/' + dir_name + "/%d_%d_%d%s.%s" % (patch.lod, patch.y, patch.x, self.channel, self.ext)

class SpaceEngineTextureSourceFactory(TextureSourceFactory):
    def create_source(self, filename, context=defaultDirContext):
        filename = context.find_texture(filename)
        if os.path.isdir(filename):
            all_faces = True
            for face in SpaceEngineVirtualTextureSource.face_str:
                if not os.path.isdir(os.path.join(filename, face)):
                    all_faces = False
            if all_faces:
                channel = None
                if os.path.exists(os.path.join(filename, 'base.jpg')):
                    channel = ''
                elif os.path.exists(os.path.join(filename, 'base_c.jpg')):
                    channel = 'c'
                return SpaceEngineVirtualTextureSource(filename, 'jpg', 258, channel)
        return None

#TODO: Should be done in Cosmonium main class
AutoTextureSource.register_source_factory(SpaceEngineTextureSourceFactory(), [], 1)
