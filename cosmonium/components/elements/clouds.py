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


from panda3d.core import CullFaceAttrib, DepthOffsetAttrib
from panda3d.core import LQuaternion

from ...shapes import ShapeObject, SphereShape
from ...surfaces import EllipsoidFlatSurface
from ...parameters import AutoUserParameter

from ... import settings


class Clouds(EllipsoidFlatSurface):
    def __init__(self, height, appearance, shader=None, shape=None):
        if shape is None:
            shape = SphereShape()
        EllipsoidFlatSurface.__init__(self, 'clouds', shape=shape, appearance=appearance, shader=shader, clickable=False)
        self.height = height
        self.scale_base = None
        self.inside = None
        self.body = None
        if appearance is not None:
            #TODO: Disabled as it causes blinking
            pass#appearance.check_transparency()
 
    def get_component_name(self):
        return _('Clouds')

    def set_body(self, body):
        self.body = body

    def configure_render_order(self):
        self.instance.set_bin("transparent", 0)

    def configure_shape(self):
        self.radius = self.body.surface.get_average_radius() + self.height
        #TODO : temporary until height_scale is removed from patchedshape
        self.height_scale = self.radius
        scale = self.body.surface.get_scale()
        factor = 1.0 + self.height / self.body.surface.get_average_radius()
        self.shape.set_scale(scale * factor)

    def check_settings(self):
        self.set_shown(settings.show_clouds)

    def update_instance(self, scene_manager, camera_pos, camera_rot):
        if not self.instance_ready: return
        self.instance.set_quat(LQuaternion(*self.body.anchor.get_absolute_orientation()))

        inside = self.body.anchor.distance_to_obs < self.radius
        if self.inside != inside:
            if inside:
                self.instance.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise))
                self.instance.setAttrib(DepthOffsetAttrib.make(0))
                if self.appearance.transparency:
                    self.instance.set_depth_write(True)
            else:
                self.instance.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullClockwise))
                if settings.use_inverse_z:
                    self.instance.setAttrib(DepthOffsetAttrib.make(-1))
                else:
                    self.instance.setAttrib(DepthOffsetAttrib.make(1))
                if self.appearance.transparency:
                    self.instance.set_depth_write(False)
            self.inside = inside
        return EllipsoidFlatSurface.update_instance(self, scene_manager, camera_pos, camera_rot)

    def remove_instance(self):
        EllipsoidFlatSurface.remove_instance(self)
        self.inside = None

    def set_height(self, height):
        self.height = height

    def get_height(self):
        return self.height

    def get_user_parameters(self):
        group = ShapeObject.get_user_parameters(self)
        group.add_parameter(AutoUserParameter('Height', 'height', self, AutoUserParameter.TYPE_FLOAT, [0, self.body.get_apparent_radius() * 0.01]))
        return group

    def update_user_parameters(self):
        ShapeObject.update_user_parameters(self)
        self.configure_shape()
