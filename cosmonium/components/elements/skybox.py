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


from panda3d.core import LVector3d

from ...appearances import Appearance
from ...shapes.shape_object import ShapeObject
from ...shapes.mesh import MeshShape
from ...utils import TransparencyBlend


class SkyBox(ShapeObject):
    def __init__(self, scattering, shape=None, appearance=None, shader=None):
        self.scattering = scattering
        if shape is None:
            shape = MeshShape(
                'ralph-data/models/rgbCube', panda=True, auto_scale_mesh=False, scale=LVector3d(32768, 32768, 32768)
            )
        if appearance is None:
            appearance = Appearance()
        ShapeObject.__init__(self, 'skybox', shape=shape, appearance=appearance, shader=shader, clickable=False)
        self.blend = TransparencyBlend.TB_Additive
        scattering.add_shape_object(self, atmosphere=True)

    def get_component_name(self):
        return _('Atmosphere')

    def configure_render_order(self):
        self.instance.set_bin("background", 1)

    async def create_instance_task(self, scene_anchor):
        await ShapeObject.create_instance_task(self, scene_anchor)
        TransparencyBlend.apply(self.blend, self.instance)
        self.instance.set_depth_write(False)
        self.instance.set_depth_test(False)
        self.instance.set_two_sided(True)

    def update_shader_params(self):
        pass

    def update_user_parameters(self):
        ShapeObject.update_user_parameters(self)
        self.update_scattering()

    def remove_instance(self):
        ShapeObject.remove_instance(self)
        self.inside = None
        for shape_object in self.attenuated_objects:
            self.remove_scattering_on(shape_object)
        self.attenuated_objects = []
        self.context.observer.has_scattering = False
        self.context.observer.scattering = None
        self.context.observer.apply_scattering = 0
