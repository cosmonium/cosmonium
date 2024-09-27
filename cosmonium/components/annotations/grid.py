#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2022 Laurent Deru.
#
# Cosmonium is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Cosmonium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#

from math import sin, cos, pi
from panda3d.core import LQuaternion, OmniBoundingVolume
from panda3d.core import GeomVertexFormat, GeomVertexData, GeomVertexWriter
from panda3d.core import Geom, GeomNode, GeomLines
from panda3d.core import NodePath

from ...appearances import ModelAppearance
from ...foundation import VisibleObject
from ...shaders.rendering import RenderingShader
from ...shaders.lighting.flat import FlatLightingModel
from ...utils import srgb_to_linear
from ... import settings


class Grid(VisibleObject):
    ignore_light = True
    default_shown = False
    shader = None
    default_camera_mask = VisibleObject.AnnotationCameraFlag

    def __init__(self, name, orientation, color):
        VisibleObject.__init__(self, name)
        self.nbOfPoints = 360
        self.nbOfRings = 17
        self.nbOfSectors = 24
        self.points_to_remove = (self.nbOfPoints // (self.nbOfRings + 1)) // 2
        self.orientation = orientation
        self.color = color
        self.settings_attr = 'show_' + name.lower() + '_grid'

    def check_settings(self):
        show = getattr(settings, self.settings_attr)
        if show is not None:
            self.set_shown(show)

    @classmethod
    def create_shader(cls):
        cls.appearance = ModelAppearance()
        cls.appearance.has_vertex_color = True
        cls.appearance.has_material = False
        cls.shader = RenderingShader(lighting_model=FlatLightingModel())
        cls.shader.color_picking = False
        cls.shader.create(None, cls.appearance)

    def create_instance(self):
        self.vertexData = GeomVertexData('vertexData', GeomVertexFormat.getV3c4(), Geom.UHStatic)
        self.vertexWriter = GeomVertexWriter(self.vertexData, 'vertex')
        self.colorwriter = GeomVertexWriter(self.vertexData, 'color')
        # TODO: This sould be simply drawn in the background bin
        infinity = self.context.scene_manager.infinity
        for r in range(1, self.nbOfRings + 1):
            for i in range(self.nbOfPoints):
                angle = 2 * pi / self.nbOfPoints * i
                x = cos(angle) * sin(pi * r / (self.nbOfRings + 1))
                y = sin(angle) * sin(pi * r / (self.nbOfRings + 1))
                z = sin(-pi / 2 + pi * r / (self.nbOfRings + 1))

                self.vertexWriter.addData3f((infinity * x, infinity * y, infinity * z))
                if r == self.nbOfRings / 2 + 1:
                    self.colorwriter.addData4(srgb_to_linear((self.color.x * 1.5, 0, 0, 1)))
                else:
                    self.colorwriter.addData4(srgb_to_linear(self.color))
        for s in range(self.nbOfSectors):
            for i in range(self.points_to_remove, self.nbOfPoints // 2 - self.points_to_remove + 1):
                angle = 2 * pi / self.nbOfPoints * i
                x = cos(2 * pi * s / self.nbOfSectors) * sin(angle)
                y = sin(2 * pi * s / self.nbOfSectors) * sin(angle)
                z = cos(angle)

                self.vertexWriter.addData3f((infinity * x, infinity * y, infinity * z))
                if s == 0:
                    self.colorwriter.addData4(srgb_to_linear((self.color.x * 1.5, 0, 0, 1)))
                else:
                    self.colorwriter.addData4(srgb_to_linear(self.color))
        self.lines = GeomLines(Geom.UHStatic)
        index = 0
        for r in range(self.nbOfRings):
            for i in range(self.nbOfPoints - 1):
                self.lines.addVertex(index)
                self.lines.addVertex(index + 1)
                self.lines.closePrimitive()
                index += 1
            self.lines.addVertex(index)
            self.lines.addVertex(index - self.nbOfPoints + 1)
            self.lines.closePrimitive()
            index += 1
        for r in range(self.nbOfSectors):
            for i in range(self.nbOfPoints // 2 - self.points_to_remove * 2):
                self.lines.addVertex(index)
                self.lines.addVertex(index + 1)
                self.lines.closePrimitive()
                index += 1
            index += 1
        self.geom = Geom(self.vertexData)
        self.geom.addPrimitive(self.lines)
        self.node = GeomNode("grid")
        self.node.addGeom(self.geom)
        self.instance = NodePath(self.node)
        if self.shader is None:
            self.create_shader()
        self.appearance.apply(self, self.instance)
        self.shader.apply(self.instance)
        self.instance.setRenderModeThickness(settings.grid_thickness)
        self.instance.reparentTo(self.scene_anchor.unshifted_instance)
        self.instance.setQuat(LQuaternion(*self.orientation))
        self.instance.setBin('background', settings.grid_depth)
        self.instance.set_depth_write(False)
        self.instance.node().setBounds(OmniBoundingVolume())
        self.instance.node().setFinal(True)
        self.instance.hide(self.AllCamerasMask)
        self.instance.show(self.default_camera_mask)

    def set_orientation(self, orientation):
        self.orientation = orientation
        if self.instance:
            self.instance.setQuat(LQuaternion(*self.orientation))
