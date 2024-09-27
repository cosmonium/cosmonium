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


from panda3d.core import LQuaternion, OmniBoundingVolume

from ...foundation import VisibleObject
from ...mesh import load_panda_model_sync
from ... import settings


class ReferenceAxes(VisibleObject):
    default_shown = False
    ignore_light = True
    default_camera_mask = VisibleObject.AnnotationCameraFlag

    def __init__(self, body):
        VisibleObject.__init__(self, body.get_ascii_name() + '-axis')
        self.body = body
        self.model = "zup-axis"

    def check_settings(self):
        self.set_shown(settings.show_reference_axis)

    def create_instance(self):
        if self.instance is not None:
            return self.instance
        self.instance = load_panda_model_sync(self.model)
        self.instance.reparent_to(self.scene_anchor.unshifted_instance)
        self.instance.set_light_off(1)
        self.instance.node().setBounds(OmniBoundingVolume())
        self.instance.node().setFinal(True)
        self.instance.hide(self.AllCamerasMask)
        self.instance.show(self.default_camera_mask)
        return self.instance

    def update_instance(self, scene_manager, camera_pos, camera_rot):
        if self.instance:
            self.instance.set_quat(LQuaternion(*self.body.anchor.get_absolute_orientation()))
            self.instance.set_scale(*self.get_scale())

    def get_scale(self):
        return self.body.surface.get_scale() / 5.0
