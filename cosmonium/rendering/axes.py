#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2026 Laurent Deru.
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


from ..components.annotations.reference_axes import ReferenceAxes
from ..components.annotations.rotation_axis import RotationAxis


class Axes:
    def __init__(self):
        self.axes = dict()

    def add_axis(self, stellar_object):
        if not stellar_object.stellar_object:
            return
        axis = []
        if stellar_object.has_rotation_axis:
            rotation_axis = RotationAxis(stellar_object)
            rotation_axis.set_scene_anchor(stellar_object.scene_anchor)
            rotation_axis.set_parent(stellar_object)
            rotation_axis.check_settings()
            axis.append(rotation_axis)
        if stellar_object.has_reference_axis:
            reference_axes = ReferenceAxes(stellar_object)
            reference_axes.set_scene_anchor(stellar_object.scene_anchor)
            reference_axes.set_parent(stellar_object)
            reference_axes.check_settings()
            axis.append(reference_axes)
        if axis:
            self.axes[stellar_object] = axis

    def remove_axis(self, stellar_object):
        if stellar_object not in self.axes:
            return
        for axis in self.axes.pop(stellar_object):
            axis.remove_instance()

    def check_settings(self):
        for axes in self.axes.values():
            for axis in axes:
                axis.check_settings()

    def check_visibility(self, frustum, pixel_size):
        for axes in self.axes.values():
            for axis in axes:
                axis.check_visibility(frustum, pixel_size)

    def check_and_create_instance(self, scene_manager, camera_pos, camera_rot):
        for axes in self.axes.values():
            for axis in axes:
                axis.check_and_create_instance(scene_manager, camera_pos, camera_rot)

    def check_and_update_instance(self, scene_manager, camera_pos, camera_rot):
        for axes in self.axes.values():
            for axis in axes:
                axis.check_and_update_instance(scene_manager, camera_pos, camera_rot)
