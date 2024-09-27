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


from panda3d.core import LQuaternion

from ...shadows import RingShadowCaster
from ...shapes.rings import RingsShape
from ...shapes.shape_object import ShapeObject


class Rings(ShapeObject):
    def __init__(self, inner_radius, outer_radius, appearance=None, shader=None):
        ShapeObject.__init__(self, 'ring', appearance=appearance, shader=shader, clickable=True)
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius
        self.set_shape(RingsShape(inner_radius, outer_radius))
        self.body = None
        self.shape.vanish_borders = True

    def get_component_name(self):
        return _('Rings')

    def set_body(self, body):
        self.body = body

    def do_create_shadow_caster_for(self, light_source):
        return RingShadowCaster(light_source, self)

    def update_instance(self, scene_manager, camera_pos, camera_rot):
        ShapeObject.update_instance(self, scene_manager, camera_pos, camera_rot)
        if not self.instance_ready:
            return
        self.instance.set_quat(LQuaternion(*self.body.anchor.get_absolute_orientation()))
