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


from panda3d.core import GeomNode
from panda3d.core import NodePath

from ..geometry import geometry

from .base import Shape


class RingsShape(Shape):
    def __init__(self, inner_radius, outer_radius):
        Shape.__init__(self)
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius
        self.nbOfPoints = 360
        self.coord = 0 #TexCoord.Flat

    def is_spherical(self):
        return False

    async def create_instance(self):
        self.instance = NodePath("ring")
        node = GeomNode('ring-up')
        node.addGeom(geometry.RingFaceGeometry(1.0, self.inner_radius, self.outer_radius, self.nbOfPoints))
        up = self.instance.attach_new_node(node)
        up.setDepthOffset(-1)
        node = GeomNode('ring-down')
        node.addGeom(geometry.RingFaceGeometry(-1.0, self.inner_radius, self.outer_radius, self.nbOfPoints))
        down = self.instance.attach_new_node(node)
        down.setDepthOffset(-1)
        self.apply_owner()
        self.instance.set_depth_write(False)
        return self.instance
