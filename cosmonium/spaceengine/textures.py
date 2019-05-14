from __future__ import print_function

from cosmonium.textures import VirtualTextureSource

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
