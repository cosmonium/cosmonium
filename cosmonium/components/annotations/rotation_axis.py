#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
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


from panda3d.core import LPoint3d, LQuaternion, OmniBoundingVolume
from panda3d.core import GeomVertexFormat, GeomVertexData, GeomVertexWriter
from panda3d.core import Geom, GeomNode, GeomLines
from panda3d.core import NodePath

from ...foundation import VisibleObject
from ...utils import srgb_to_linear
from ... import settings


class RotationAxis(VisibleObject):
    default_shown = False
    ignore_light = True
    default_camera_mask = VisibleObject.AnnotationCameraFlag

    def __init__(self, body):
        VisibleObject.__init__(self, body.get_ascii_name() + '-axis')
        self.body = body

    def create_instance(self):
        self.vertexData = GeomVertexData('vertexData', GeomVertexFormat.getV3(), Geom.UHStatic)
        self.vertexWriter = GeomVertexWriter(self.vertexData, 'vertex')
        radius = 1.0
        top = LPoint3d(0, 0, radius * 1.25)
        north_pole = LPoint3d(0, 0, radius)
        south_pole = LPoint3d(0, 0, -radius)
        bottom = LPoint3d(0, 0, -radius * 1.25)
        self.vertexWriter.addData3f(*top)
        self.vertexWriter.addData3f(*north_pole)
        self.vertexWriter.addData3f(*south_pole)
        self.vertexWriter.addData3f(*bottom)
        self.lines = GeomLines(Geom.UHStatic)
        self.lines.addVertex(0)
        self.lines.addVertex(1)
        self.lines.addVertex(2)
        self.lines.addVertex(3)
        self.lines.closePrimitive()
        self.geom = Geom(self.vertexData)
        self.geom.addPrimitive(self.lines)
        self.node = GeomNode(self.body.get_ascii_name() + '-axis')
        self.node.addGeom(self.geom)
        self.instance = NodePath(self.node)
        self.instance.setRenderModeThickness(settings.axis_thickness)
        self.instance.setColor(srgb_to_linear(self.body.get_orbit_color()))
        self.instance.reparentTo(self.scene_anchor.unshifted_instance)
        self.instance.set_light_off(1)
        self.instance.node().setBounds(OmniBoundingVolume())
        self.instance.node().setFinal(True)
        self.instance.hide(self.AllCamerasMask)
        self.instance.show(self.default_camera_mask)

    def check_settings(self):
        self.set_shown(settings.show_rotation_axis)

    def check_visibility(self, frustum, pixel_size):
        if self.parent.shown:
            distance_to_obs = self.body.anchor.distance_to_obs
            if distance_to_obs > 0.0:
                size = self.body.get_apparent_radius() / (distance_to_obs * pixel_size)
            else:
                size = 0.0
            self.visible = size > settings.axis_fade
        else:
            self.visible = False

    def update_instance(self, scene_manager, camera_pos, camera_rot):
        if self.instance is not None:
            self.instance.set_scale(*self.get_scale())
            self.instance.set_quat(LQuaternion(*self.body.anchor.get_absolute_orientation()))

    def get_scale(self):
        return self.body.surface.get_scale()
