from __future__ import print_function
from __future__ import absolute_import

from ..surfaces import FlatSurface
from ..patchedshapes import SquaredDistanceSquareShape, VertexSizePatchLodControl
from ..shaders import BasicShader, FlatLightingModel
from ..appearances import Appearance
from ..textures import SurfaceTexture
from ..bodies import SurfaceFactory

from .textures import ProceduralVirtualTextureSource

class ProceduralStarSurfaceFactory(SurfaceFactory):
    def __init__(self, noise, size=256):
        SurfaceFactory.__init__(self)
        self.size = size
        self .noise = noise

    def create(self, body):
        shape = SquaredDistanceSquareShape(patch_size_from_texture=False,
                                                lod_control=VertexSizePatchLodControl(max_vertex_size=64),
                                                use_shader=False)
        shader = BasicShader(lighting_model=FlatLightingModel())
        surface = FlatSurface(appearance=Appearance(emissionColor=body.point_color,
                                                    texture=SurfaceTexture(ProceduralVirtualTextureSource(self.noise, self.size))),
                              shape=shape,
                              shader=shader)
        return surface

class ProceduralStarSurfaceFactoryDB(object):
    def __init__(self):
        self.factories = {}

    def add(self, name, factory):
        self.factories[name] = factory

    def get(self, name):
        return self.factories.get(name)

proceduralStarSurfaceFactoryDB = ProceduralStarSurfaceFactoryDB()
