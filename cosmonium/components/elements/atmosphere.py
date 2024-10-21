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


from panda3d.core import CullFaceAttrib
from panda3d.core import LQuaternion

from ...shapes.shape_object import ShapeObject
from ...utils import TransparencyBlend

from ... import settings


class Atmosphere(ShapeObject):
    def __init__(self, scattering, shape, appearance, shader):
        ShapeObject.__init__(self, 'atmosphere', shape=shape, appearance=appearance, shader=shader, clickable=False)
        self.scattering = scattering
        self.inside = None
        self.body = None
        self.radius = None
        self.blend = TransparencyBlend.TB_Additive
        scattering.add_shape_object(self, atmosphere=True)

    def add_shape_object(self, shape_object):
        self.scattering.add_shape_object(shape_object)

    def get_component_name(self):
        return _('Atmosphere')

    def configure_render_order(self):
        self.instance.set_bin("transparent", 0)

    def set_body(self, body):
        self.body = body
        self.scattering.set_body(body)
        self.radius = self.scattering.radius
        self.body_radius = self.scattering.body_radius
        self.ratio = self.scattering.ratio

    def check_settings(self):
        if settings.show_atmospheres != self.shown:
            if self.shown:
                self.scattering.disable_scattering()
            else:
                self.scattering.enable_scattering()
        self.set_shown(settings.show_atmospheres)

    def get_pixel_height(self):
        return self.body.anchor.visible_size * (self.ratio - 1.0)

    def check_visibility(self, frustum, pixel_size):
        ShapeObject.check_visibility(self, frustum, pixel_size)
        if self.get_pixel_height() < 1.0:
            self.visible = False

    async def create_instance_task(self, scene_anchor):
        # TODO: Find a better way to retrieve ellipticity
        scale = self.body.surface.get_scale() / self.body_radius
        self.set_scale(scale * self.radius)
        await ShapeObject.create_instance_task(self, scene_anchor)
        TransparencyBlend.apply(self.blend, self.instance)
        self.instance.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise))
        self.instance.set_depth_write(False)

    def update_shader_params(self):
        pass

    def update_obs(self, observer):
        ShapeObject.update_obs(self, observer)
        inside = self.body.anchor.distance_to_obs < self.radius
        if self.inside != inside:
            self.inside = inside
            self.scattering.set_inside(self.inside)
            if self.inside:
                print("Entering atmosphere")
                observer.has_scattering = True
                observer.scattering = self.scattering
                # TODO: To replace with a flag once update_id is merged in
                observer.apply_scattering = 5
            else:
                print("Leaving atmosphere")
                self.scattering.remove_all_attenuated_objects()
                observer.has_scattering = False
                observer.scattering = None
                observer.apply_scattering = 0
        elif observer.apply_scattering > 0:
            observer.apply_scattering -= 1

    def update_user_parameters(self):
        ShapeObject.update_user_parameters(self)
        self.scattering.update_user_parameters()

    def get_user_parameters(self):
        group = ShapeObject.get_user_parameters(self)
        group.add_parameters(self.scattering.get_user_parameters())
        return group

    def update_instance(self, scene_manager, camera_pos, camera_rot):
        ShapeObject.update_instance(self, scene_manager, camera_pos, camera_rot)
        if not self.instance_ready:
            return
        self.instance.set_quat(LQuaternion(*self.body.anchor.get_absolute_orientation()))

    def remove_instance(self):
        ShapeObject.remove_instance(self)
        self.inside = None
        self.scattering.clear()
        self.context.observer.has_scattering = False
        self.context.observer.scattering = None
        self.context.observer.apply_scattering = 0
