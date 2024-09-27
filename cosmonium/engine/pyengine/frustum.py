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


from panda3d.core import LPlaned


class InfiniteFrustum(object):
    def __init__(self, frustum, view_mat, view_position, zero_near=True):
        self.planes = []
        self.position = view_position
        # Panda3D frustum has side planes stored from 1 to 4, far plane is 0 and near plane is 5
        # To make an infinite frustum, we drop the far plane
        for i in range(5):
            plane = frustum.get_plane(i + 1)
            if zero_near and i == 4:
                # Set the distance of the near plane to 0
                plane[3] = 0.0
            plane *= view_mat
            new_plane = LPlaned()
            new_plane[0] = plane[0]
            new_plane[1] = plane[1]
            new_plane[2] = plane[2]
            new_plane[3] = plane[3] - view_position.length()
            self.planes.append(new_plane)

    def is_sphere_in(self, center, radius):
        for plane in self.planes:
            dist = plane.dist_to_plane(center)
            if dist > radius:
                return False
        return True

    def get_position(self):
        return self.position

    def __str__(self):
        return "InfiniteFrustum " + str(self.planes)
