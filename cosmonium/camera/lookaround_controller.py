#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2025 Laurent Deru.
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


from math import pi

from panda3d.core import LPoint3d, LQuaterniond, LVector3d

from .base import BaseCameraController


class LookAroundCameraController(BaseCameraController):
    camera_mode = BaseCameraController.LOOK_AROUND

    def get_name(self):
        return _('Look around camera')

    def get_id(self):
        return "look-around"

    def set_camera_hints(self, **kwargs):
        self.reference_position = kwargs.get('position', LPoint3d())
        self.reference_orientation = kwargs.get('rotation', LQuaterniond())

    def update(self, time, dt):
        if self.base.mouseWatcherNode.hasMouse():
            mpos = self.base.mouseWatcherNode.getMouse()
            x_angle = mpos.get_y() * pi / 2
            z_angle = mpos.get_x() * pi / 2
            x_rotation = LQuaterniond()
            x_rotation.setFromAxisAngleRad(x_angle, LVector3d.right())
            z_rotation = LQuaterniond()
            z_rotation.setFromAxisAngleRad(-z_angle, LVector3d.up())
            self._frame_orientation = x_rotation * z_rotation

        self.camera.change_global(self.reference_anchor.get_absolute_reference_point())
        self.camera.set_local_position(self.get_local_position())
        self.camera.set_absolute_orientation(self.get_local_orientation())
        self.camera.update()
