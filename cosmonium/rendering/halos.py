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


from .. import settings
from ..components.elements.halo import Halo


class Halos:
    """Registry of the halos of the resolved objects."""

    def __init__(self):
        self.halo_objects = dict()

    def add_halo(self, anchor):
        if anchor not in self.halo_objects and not settings.use_pbr and anchor.body.has_resolved_halo:
            stellar_object = anchor.body
            halo = Halo(stellar_object)
            halo.set_scene_anchor(anchor.scene_anchor)
            halo.set_parent(stellar_object)
            halo.check_settings()
            self.halo_objects[anchor] = halo

    def remove_halo(self, anchor):
        if anchor not in self.halo_objects:
            return
        halo = self.halo_objects.pop(anchor)
        halo.remove_instance()

    def check_settings(self):
        for halo in self.halo_objects.values():
            halo.check_settings()

    def check_visibility(self, frustum, pixel_size):
        for halo in self.halo_objects.values():
            halo.check_visibility(frustum, pixel_size)

    def check_and_create_instance(self, scene_manager, camera_pos, camera_rot):
        for halo in self.halo_objects.values():
            halo.check_and_create_instance(scene_manager, camera_pos, camera_rot)

    def check_and_update_instance(self, scene_manager, camera_pos, camera_rot):
        for halo in self.halo_objects.values():
            halo.check_and_update_instance(scene_manager, camera_pos, camera_rot)
