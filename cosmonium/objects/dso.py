#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2022 Laurent Deru.
#
#Cosmonium is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Cosmonium is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#


from .emissive import EmissiveBody

from ..astro import units


class DeepSpaceObject(EmissiveBody):
    background = True
    has_rotation_axis = False
    has_reference_axis = False
    has_resolved_halo = False
    support_offset_body_center = False

    def __init__(self, names, source_names, radius, radius_units=units.Ly,
                 abs_magnitude=None,
                 surface=None,
                 orbit=None, rotation=None,
                 body_class=None, point_color=None,
                 description=''):
        radius = radius * radius_units
        EmissiveBody.__init__(self, names, source_names, radius=radius,
                              surface=surface,
                              orbit=orbit, rotation=rotation,
                              abs_magnitude=abs_magnitude,
                              body_class=body_class, point_color=point_color,
                              description=description)

    def get_height_under(self, position):
        return 0.0

    def check_and_update_instance(self, scene_manager, camera_pos, camera_rot):
        EmissiveBody.check_and_update_instance(self, scene_manager, camera_pos, camera_rot)
        app_magnitude = self.get_app_magnitude()
        self.surface.appearance.set_magnitude(self, self.surface.shape, self.surface.shader, self.anchor._abs_magnitude, app_magnitude, self.anchor.visible_size)
