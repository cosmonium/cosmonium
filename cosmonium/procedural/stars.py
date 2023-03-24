#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2023 Laurent Deru.
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


from math import pi

from ..astro import units
from ..components.elements.surfaces import EllipsoidFlatSurface
from ..patchedshapes import SquaredDistanceSquareShape, SquaredDistanceSquarePatchFactory, VertexSizeLodControl
from ..shaders.rendering import RenderingShader
from ..shaders.lighting.flat import FlatLightingModel
from ..appearances import Appearance
from ..textures import SurfaceTexture
from ..objects.surface_factory import SurfaceFactory
from .. import settings

from .textures import NoiseTextureGenerator, PatchedProceduralVirtualTextureSource
from .shadernoise import GrayTarget

class ProceduralStarSurfaceFactory(SurfaceFactory):
    def __init__(self, noise, size=256):
        SurfaceFactory.__init__(self)
        self.size = size
        self.noise = noise
        self.target = GrayTarget()

    def create(self, body):
        factory = SquaredDistanceSquarePatchFactory()
        lod_control = VertexSizeLodControl(max_vertex_size=settings.patch_max_vertex_size,
                                           density=settings.patch_constant_density)
        shape = SquaredDistanceSquareShape(factory, lod_control=lod_control)
        shader = RenderingShader(lighting_model=FlatLightingModel())
        tex_generator = NoiseTextureGenerator(self.size, self.noise, self.target, alpha=False, srgb=False)
        if settings.use_pbr:
            radiance = body.anchor.get_radiant_flux() / (4 * pi * pi * body.radius * body.radius / units.m / units.m)
        else:
            radiance = 1.0
        surface = EllipsoidFlatSurface(radius=body.radius, oblateness=body.oblateness, scale=body.scale,
                              appearance=Appearance(colorScale=body.anchor.point_color * radiance,
                                                    texture=SurfaceTexture(PatchedProceduralVirtualTextureSource(tex_generator,
                                                                                                                 self.size),
                                                                           srgb=False)),
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
