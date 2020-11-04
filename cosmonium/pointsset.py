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

from panda3d.core import GeomVertexArrayFormat, InternalName, GeomVertexFormat, GeomVertexData, GeomVertexWriter
from panda3d.core import GeomPoints, Geom, GeomNode
from panda3d.core import NodePath, OmniBoundingVolume, DrawMask
from .foundation import VisibleObject
from .appearances import ModelAppearance
from .shaders import BasicShader, FlatLightingModel, StaticSizePointControl
from .sprites import SimplePoint, RoundDiskPointSprite

class PointsSet(VisibleObject):
    tex = None
    def __init__(self, use_sprites=True, use_sizes=True, points_size=2, sprite=None, background=None, shader=None):
        self.gnode = GeomNode('starfield')
        self.use_sprites = use_sprites
        self.use_sizes = use_sizes
        self.use_oids = True
        self.background = background
        if shader is None:
            shader = BasicShader(lighting_model=FlatLightingModel(), vertex_oids=True)
        self.shader = shader

        self.reset()

        self.geom = self.makeGeom([], [], [], [])
        self.gnode.addGeom(self.geom)
        self.instance = NodePath(self.gnode)
        if self.use_sprites:
            if sprite is None:
                sprite = RoundDiskPointSprite()
            self.sprite = sprite
        else:
            self.sprite = SimplePoint(points_size)
        self.sprite.apply(self.instance)
        self.instance.setCollideMask(GeomNode.getDefaultCollideMask())
        self.instance.node().setPythonTag('owner', self)
        #TODO: Should not use ModelAppearance !
        self.appearance = ModelAppearance(vertex_color=True)
        if self.appearance is not None:
            self.appearance.bake()
            self.appearance.apply(self, self)
        if self.shader is not None:
            self.shader.apply(self, self.appearance)
        if self.use_sprites:
            self.instance.node().setBounds(OmniBoundingVolume())
            self.instance.node().setFinal(True)
        if self.background is not None:
            self.instance.setBin('background', self.background)
        self.instance.set_depth_write(False)
        self.instance.hide(self.AllCamerasMask)
        self.instance.show(self.DefaultCameraMask)

    def jobs_done_cb(self, patch):
        pass

    def reset(self):
        self.points = []
        self.colors = []
        self.sizes = []
        self.oids = []

    def add_point(self, position, color, size, oid):
        self.points.append(position)
        self.colors.append(color)
        self.sizes.append(size)
        self.oids.append(oid)

    def update(self):
        self.update_arrays(self.points, self.colors, self.sizes, self.oids)

    def makeGeom(self, points, colors, sizes, oids):
        array = GeomVertexArrayFormat()
        array.addColumn(InternalName.get_vertex(), 3, Geom.NTFloat32, Geom.CPoint)
        array.addColumn(InternalName.get_color(), 4, Geom.NTFloat32, Geom.CColor)
        if self.use_sizes:
            array.addColumn(InternalName.get_size(), 1, Geom.NTFloat32, Geom.COther)
        if self.use_oids:
            oids_column_name = InternalName.make('oid')
            array.addColumn(oids_column_name, 4, Geom.NTFloat32, Geom.COther)
        format = GeomVertexFormat()
        format.addArray(array)
        format = GeomVertexFormat.registerFormat(format)
        vdata = GeomVertexData('vdata', format, Geom.UH_static)
        vdata.unclean_set_num_rows(len(points))
        self.vwriter = GeomVertexWriter(vdata, InternalName.get_vertex())
        self.colorwriter = GeomVertexWriter(vdata, InternalName.get_color())
        if self.use_sizes:
            self.sizewriter = GeomVertexWriter(vdata, InternalName.get_size())
        if self.use_oids:
            self.oidwriter = GeomVertexWriter(vdata, oids_column_name)
        geompoints = GeomPoints(Geom.UH_static)
        geompoints.reserve_num_vertices(len(points))
        index = 0
        for (point, color, size, oid) in zip(points, colors, sizes, oids):
            self.vwriter.addData3f(*point)
            #self.colorwriter.addData3f(color[0], color[1], color[2])
            self.colorwriter.addData4(color)
            if self.use_sizes:
                self.sizewriter.addData1f(size)
            if self.use_oids:
                self.oidwriter.addData4(oid)
            geompoints.addVertex(index)
            geompoints.closePrimitive()
            index += 1
        geom = Geom(vdata)
        geom.addPrimitive(geompoints)
        return geom

    def update_arrays(self, points, colors, sizes, oids):
        self.gnode.removeAllGeoms()
        self.geom = self.makeGeom(points, colors, sizes, oids)
        self.gnode.addGeom(self.geom)
