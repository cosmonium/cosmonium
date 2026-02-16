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

"""Shadow projector for projection calculations and camera alignment.

This module provides the ShadowProjector class which handles shadow projection
calculations, frustum computations, and camera alignment for reducing flickering.
"""

from __future__ import annotations

from panda3d.core import LPoint3, LPoint4, LVector3, LVector3d, Mat4, NodePath, OrthographicLens, TransformState


class ShadowProjector:
    """Handles shadow projection calculations and camera alignment.

    This class encapsulates logic for computing projection matrices,
    aligning shadow cameras, and managing shadow frustums.
    """

    def __init__(self) -> None:
        """Initialize the shadow projector."""
        pass

    def align_shadow_camera(self, base_render: NodePath, cam: NodePath, size: int, lens: OrthographicLens) -> LPoint3:
        """Align shadow camera to texel grid to reduce shadow flickering.

        This snaps the shadow camera position to the texel grid to ensure
        consistent shadow sampling when the camera moves.

        Returns:
            The adjusted camera position.
        """
        # Calculate model-view-projection matrix
        mvp = Mat4(base_render.get_transform(cam).get_mat() * lens.get_projection_mat())

        # Transform center point to NDC space
        center = mvp.xform(LPoint4(0, 0, 0, 1)) * 0.5 + 0.5

        # Calculate texel size
        texel_size = 1.0 / size

        # Calculate offset to nearest texel
        offset_x = center.x % texel_size
        offset_y = center.y % texel_size

        # Transform back to world space
        mvp.invert_in_place()
        new_center = mvp.xform(
            LPoint4((center.x - offset_x) * 2.0 - 1.0, (center.y - offset_y) * 2.0 - 1.0, (center.z) * 2.0 - 1.0, 1.0)
        )

        # Calculate and apply offset
        offset = LVector3(new_center.x, new_center.y, new_center.z)
        adjusted_pos = cam.get_pos() - offset
        cam.set_pos(adjusted_pos)

        return adjusted_pos

    def update_lens(self, lens: OrthographicLens, occluder_radius: float, light_direction: LVector3d) -> None:
        """Compute shadow frustum parameters for an occluder.

        Args:
            lens: The camera lens.
            occluder_radius: Bounding radius of the shadow-casting object.
            light_direction: Direction vector to the light (should be normalized for consistent results).
        """
        # Film size should be slightly larger than occluder to avoid clipping
        film_size = occluder_radius * 2.1

        # Near plane at 0 (at occluder boundary)
        near = 0.0

        # Far plane at twice the radius
        far = occluder_radius * 2.0

        lens.set_film_size(film_size, film_size)
        lens.set_near(near)
        lens.set_far(far)
        lens.set_view_vector(LVector3(*light_direction), LVector3.up())

    def compute_light_space_matrix(self, cam_transform: TransformState, lens: OrthographicLens) -> Mat4:
        """Compute the light space transformation matrix.

        Args:
            cam_transform: The camera's transform matrix.
            lens: The camera's lens.

        Returns:
            The combined model-view-projection matrix.
        """
        return Mat4(cam_transform.get_mat() * lens.get_projection_mat())
