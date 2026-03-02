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

"""View frustum implementation for visibility culling.

This module provides the InfiniteFrustum class for determining object visibility
within the camera view. The frustum uses an infinite far plane which is essential
for space rendering where objects can be arbitrarily far away.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from panda3d.core import LPlaned

if TYPE_CHECKING:
    from panda3d.core import BoundingVolume, LMatrix4, LPoint3d


class InfiniteFrustum:
    """View frustum with infinite far plane for space rendering.

    An infinite frustum is used for visibility culling in space environments
    where objects can be arbitrarily far away. This implementation drops the
    far plane from a standard frustum, keeping only the near plane and four
    side planes.
    """

    def __init__(
        self, frustum: BoundingVolume, view_mat: LMatrix4, view_position: LPoint3d, zero_near: bool = True
    ) -> None:
        """Initialize the InfiniteFrustum by extracting and transforming the planes from the given frustum.

        Args:
            frustum: The source bounding volume representing the camera frustum.
            view_mat: The view transformation matrix.
            view_position: The position of the view/camera.
            zero_near: If True, sets the near plane distance to zero.
        """
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

    def is_sphere_in(self, center: LPoint3d, radius: float) -> bool:
        """Test if a sphere intersects or is contained within the frustum.

        Args:
            center: The center point of the sphere.
            radius: The radius of the sphere.

        Returns:
            True if the sphere is at least partially inside the frustum.
        """
        for plane in self.planes:
            dist = plane.dist_to_plane(center)
            if dist > radius:
                return False
        return True

    def get_position(self) -> LPoint3d:
        """Get the frustum's position.

        Returns:
            The position of the frustum.
        """
        return self.position

    def __str__(self) -> str:
        return "InfiniteFrustum " + str(self.planes)
