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

from __future__ import annotations

from panda3d.core import LPoint3d, LVector3d

from .base import SurfaceModelInterface


class FlatSurfaceModel(SurfaceModelInterface):
    """Surface model for a flat 2D plane terrain (no height variation)."""

    def is_flat(self) -> bool:
        return True

    def is_spherical(self) -> bool:
        # Tiled-plane shapes are treated as "spherical" in the existing codebase.
        return True

    def get_alt_under(self, position: LPoint3d, strict: bool = False) -> float | None:
        return 0

    def get_height_under(self, position: LPoint3d, strict: bool = False) -> float | None:
        return 0

    def get_point_under(self, position: LPoint3d, strict: bool = False) -> LPoint3d | None:
        return LPoint3d(position[0], position[1], 0)

    def get_tangent_plane_under(self, position: LPoint3d) -> tuple[LVector3d, LVector3d, LVector3d]:
        return (LVector3d.right(), LVector3d.forward(), LVector3d.up())

    def get_height_patch(self, patch, u, v, strict=False):
        return 0

    def get_min_radius(self) -> float:
        return 0

    def get_max_radius(self) -> float:
        return 0

    def get_average_radius(self) -> float:
        return 0

    def position_to_parametric(self, position: LPoint3d) -> tuple[float, float]:
        return (position[0], position[1])
