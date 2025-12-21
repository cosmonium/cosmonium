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
from panda3d.core import LVector3d, LQuaterniond

from .base import BaseCameraController, RotateAnchorHelper


class FixedCameraController(BaseCameraController):
    camera_mode = BaseCameraController.FIXED
    STATE_DEFAULT = 'default'
    STATE_MOUSE_DRAG = 'mouse-drag'

    def __init__(self):
        BaseCameraController.__init__(self)
        self.state = self.STATE_DEFAULT

    def get_name(self):
        return _('Fixed camera')

    def get_id(self):
        return "fixed"

    def set_camera_hints(self, **kwargs):
        reference_position = kwargs.get('position', None)
        distance = kwargs.get('distance', 5)
        if reference_position is None:
            reference_position = -LVector3d().forward() * self.reference_anchor.get_apparent_radius() * distance
        self.set_reference_position(reference_position)

    def register_events(self):
        self.accept('*', self.look_back)
        self.accept("mouse1", self.mouse_click_event)
        self.accept("mouse1-up", self.mouse_release_event)

    def mouse_click_event(self):
        if not self.state == self.STATE_DEFAULT:
            return
        self.mouse_control = RotateAnchorHelper(self.base, self.camera)
        orbit_speed_z = self.camera.lens.get_hfov() / 180 * pi / 2
        orbit_speed_x = self.camera.lens.get_vfov() / 180 * pi / 2
        self.mouse_control.start(orbit_speed_x, orbit_speed_z)
        self.state = self.STATE_MOUSE_DRAG

    def mouse_release_event(self):
        if self.state == self.STATE_MOUSE_DRAG:
            self.mouse_control = None
            self.state = self.STATE_DEFAULT

    def prepare_movement(self):
        self.reference_anchor.set_absolute_orientation(self.get_local_orientation())
        self._frame_orientation = LQuaterniond()

    def look_back(self):
        look_back_rot = LQuaterniond()
        look_back_rot.setFromAxisAngleRad(pi, LVector3d.up())
        self.set_frame_orientation(look_back_rot * self._frame_orientation)

    def update(self, time, dt):
        self.camera.change_global(self.reference_anchor.get_absolute_reference_point())
        self.camera.set_local_position(self.get_local_position())
        if self.state == self.STATE_DEFAULT:
            self.camera.set_absolute_orientation(self.get_local_orientation())
        elif self.state == self.STATE_MOUSE_DRAG:
            self.mouse_control.update()
            self.set_local_orientation(self.camera.get_absolute_orientation())
        else:
            print("Unknown state", self.state)
        self.camera.update()
