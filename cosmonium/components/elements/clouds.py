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


from panda3d.core import CullFaceAttrib, DepthOffsetAttrib, LVector3
from panda3d.core import LQuaternion

from ...parameters import AutoUserParameter
from ...shapes.shape_object import ShapeObject
from ...shapes.spheres import SphereShape
from ... import settings

from .surfaces import EllipsoidFlatSurface


class Clouds(EllipsoidFlatSurface):
    def __init__(self, height, appearance, shader=None, shape=None):
        if shape is None:
            shape = SphereShape()
        EllipsoidFlatSurface.__init__(
            self, 'clouds', shape=shape, appearance=appearance, shader=shader, clickable=False
        )
        self.height = height
        self.scale_base = None
        self.inside = None
        self.body = None
        if appearance is not None:
            # TODO: Disabled as it causes blinking
            pass  # appearance.check_transparency()

    def get_component_name(self):
        return _('Clouds')

    def set_body(self, body):
        self.body = body

    def configure_render_order(self):
        self.instance.set_bin("transparent", 0)

    def configure_shape(self):
        self.model = self.body.surface.model.copy_extend(self.height)
        self.radius = self.model.radius
        # TODO : temporary until height_scale is removed from patchedshape
        self.height_scale = self.radius
        self.shape.set_axes(self.model.get_shape_axes())
        self.shape.set_scale(LVector3(self.radius))

    def check_settings(self):
        self.set_shown(settings.show_clouds)

    def update_instance(self, scene_manager, camera_pos, camera_rot):
        if self.instance_ready:
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
        group.add_parameter(
            AutoUserParameter(
                'Height', 'height', self, AutoUserParameter.TYPE_FLOAT, [0, self.body.get_apparent_radius() * 0.01]
            )
        )
        return group

    def update_user_parameters(self):
        ShapeObject.update_user_parameters(self)
        self.configure_shape()
