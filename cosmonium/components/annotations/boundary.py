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


from panda3d.core import OmniBoundingVolume
from panda3d.core import GeomVertexFormat, GeomVertexData, GeomVertexWriter
from panda3d.core import Geom, GeomNode, GeomLines
from panda3d.core import NodePath

from ...foundation import VisibleObject
from ...bodyclass import bodyClasses
from ...shaders.rendering import RenderingShader
from ...shaders.lighting.flat import FlatLightingModel
from ...appearances import ModelAppearance
from ...utils import srgb_to_linear
from ... import settings


class Boundary(VisibleObject):
    ignore_light = True
    default_shown = True
    shader = None

    def __init__(self, name, points = [], color = None):
        VisibleObject.__init__(self, name)
        if color is None:
            color = bodyClasses.get_orbit_color('boundary')
        self.color = color
        self.points = points

    def check_settings(self):
        self.set_shown(settings.show_boundaries)

    @classmethod
    def create_shader(cls):
        cls.appearance = ModelAppearance()
        cls.appearance.has_vertex_color = True
        cls.appearance.has_material = False
        cls.shader = RenderingShader(lighting_model=FlatLightingModel())
        cls.shader.color_picking = False
        cls.shader.create(None, cls.appearance)

    def set_points_list(self, points):
        self.points = points

    def create_instance(self):
        self.vertexData = GeomVertexData('vertexData', GeomVertexFormat.getV3c4(), Geom.UHStatic)
        self.vertexWriter = GeomVertexWriter(self.vertexData, 'vertex')
        self.colorwriter = GeomVertexWriter(self.vertexData, 'color')
        infinity = self.context.scene_manager.infinity
        for point in self.points:
            position = point.project(0, self.context.observer.get_absolute_position(), infinity)
            self.vertexWriter.addData3f(*position)
            self.colorwriter.addData4(srgb_to_linear(self.color))
        self.lines = GeomLines(Geom.UHStatic)
        index = 0
        for i in range(len(self.points)-1):
            self.lines.addVertex(index)
            self.lines.addVertex(index+1)
            self.lines.closePrimitive()
            index += 1
        self.geom = Geom(self.vertexData)
        self.geom.addPrimitive(self.lines)
        self.node = GeomNode("boundary")
        self.node.addGeom(self.geom)
        self.instance = NodePath(self.node)
        if self.shader is None:
            self.create_shader()
        self.appearance.apply(self, self.instance)
        self.shader.apply(self.instance)
        self.instance.setRenderModeThickness(settings.boundary_thickness)
        self.instance.reparentTo(self.scene_anchor.unshifted_instance)
        self.instance.setBin('background', settings.boundaries_depth)
        self.instance.set_depth_write(False)
        self.instance.node().setBounds(OmniBoundingVolume())
        self.instance.node().setFinal(True)
