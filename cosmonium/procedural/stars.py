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

from ..surfaces import FlatSurface
from ..patchedshapes import SquaredDistanceSquareShape, VertexSizePatchLodControl
from ..shaders import BasicShader, FlatLightingModel
from ..appearances import Appearance
from ..textures import SurfaceTexture
from ..bodies import SurfaceFactory
from .. import settings

from .textures import ProceduralVirtualTextureSource
from .shadernoise import GrayTarget

class ProceduralStarSurfaceFactory(SurfaceFactory):
    def __init__(self, noise, size=256):
        SurfaceFactory.__init__(self)
        self.size = size
        self.noise = noise
        self.target = GrayTarget()

    def create(self, body):
        shape = SquaredDistanceSquareShape(lod_control=VertexSizePatchLodControl(max_vertex_size=settings.patch_max_vertex_size,
                                                                                 density=settings.patch_constant_density),
                                           use_shader=False)
        shader = BasicShader(lighting_model=FlatLightingModel())
        surface = FlatSurface(appearance=Appearance(colorScale=body.point_color,
                                                    texture=SurfaceTexture(ProceduralVirtualTextureSource(self.noise,
                                                                                                          self.target,
                                                                                                          self.size))),
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
