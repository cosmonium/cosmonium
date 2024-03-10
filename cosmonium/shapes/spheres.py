#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2022 Laurent Deru.
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


from panda3d.core import LVector3d, NodePath

from ..geometry import geometry
from .base import Shape


class SphereShape(Shape):

    def __init__(self):
        Shape.__init__(self)
        self.axes = LVector3d(1)
        self.radius = 1.0

    def set_axes(self, axes):
        self.axes = axes
        self.radius = max(*axes)

    async def create_instance(self):
        self.instance = geometry.UVSphere(self.axes / self.radius, rings=45, sectors=90)
        if self.use_collision_solid:
            self.create_collision_solid(self.radius)
        self.apply_owner()
        return self.instance

class IcoSphereShape(Shape):
    template = None
    def __init__(self, subdivisions=3):
        Shape.__init__(self)
        self.subdivisions = subdivisions

    async def create_instance(self):
        if self.template is None:
            self.template = geometry.IcoSphere(radius=1, subdivisions=self.subdivisions)
        self.instance = NodePath('icoshpere')
        self.template.instanceTo(self.instance)
        if self.use_collision_solid:
            self.create_collision_solid()
        self.apply_owner()
        return self.instance

class DisplacementSphereShape(Shape):
    def __init__(self, heightmap, max_height):
        Shape.__init__(self)
        self.heightmap = heightmap
        self.max_height = max_height

    async def create_instance(self):
        print(self.radius, self.max_height)
        self.instance = geometry.DisplacementUVSphere(radius=1.0,
                                                      heightmap=self.heightmap,
                                                      scale=self.max_height/self.radius,
                                                      rings=45, sectors=90)
        if self.use_collision_solid:
            self.create_collision_solid()
        self.apply_owner()
        return self.instance

class ScaledSphereShape(Shape):
    def __init__(self, radius=1.0):
        Shape.__init__(self)
        self.radius = radius

    async def create_instance(self):
        self.instance=geometry.UVSphere(radius=self.radius, rings=45, sectors=90)
        if self.use_collision_solid:
            self.create_collision_solid(self.radius)
        return self.instance
