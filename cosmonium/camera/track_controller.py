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


from panda3d.core import LVector3d

from .base import BaseCameraController


class TrackCameraController(BaseCameraController):
    camera_mode = BaseCameraController.TRACK

    def __init__(self):
        BaseCameraController.__init__(self)
        self.target = None

    def get_name(self):
        return _('Track camera')

    def get_id(self):
        return "track"

    def require_target(self):
        return True

    def set_target(self, target):
        self.target = target

    def set_camera_hints(self, **kwargs):
        reference_position = kwargs.get('position', None)
        distance = kwargs.get('distance', 5)
        if reference_position is None:
            reference_position = -LVector3d().forward() * self.reference_anchor.get_apparent_radius() * distance
        self.set_reference_position(reference_position)

    def update(self, time, dt):
        self.center_on_object(self.target, duration=0, cmd=False)

        self.camera.change_global(self.reference_anchor.get_absolute_reference_point())
        self.camera.set_local_position(self.get_local_position())
        self.camera.set_absolute_orientation(self.get_local_orientation())
        self.camera.update()
