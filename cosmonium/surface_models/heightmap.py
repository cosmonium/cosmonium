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

from __future__ import annotations

from math import ceil, floor

from panda3d.core import LPoint3d, LVector3d

from .base import SurfaceModelInterface
from .ellipsoid import EllipsoidModelInterface


class HeightmapSurfaceModel(SurfaceModelInterface):
    """
    Surface model that wraps another SurfaceModelInterface and adds heightmap
    displacement.
    """

    def __init__(self, base_model, heightmap, height_scale: float, biome=None):
        self._base = base_model
        self.heightmap = heightmap
        self._height_scale = height_scale
        self.biome = biome
        # Set by configure_with_surface() after the owning Surface is initialised.
        self._shape = None

    # --- Geometry predicates ---

    def is_flat(self) -> bool:
        return False

    def is_spherical(self) -> bool:
        return self._base.is_spherical()

    # --- Surface geometry queries ---

    def get_alt_under(self, position: LPoint3d, strict: bool = False) -> float | None:
        (x, y) = self._base.position_to_parametric(position)
        coord = self._shape.parametric_to_shape_coord(x, y)
        patch = self._shape.find_patch_at(coord)
        if patch is not None:
            u, v = patch.coord_to_uv(coord)
            height = self.get_height_patch(patch, u, v, strict)
        elif strict:
            height = None
        else:
            height = 0
        return height

    def get_height_under(self, position, strict=False) -> float | None:
        height = self.get_alt_under(position, strict)
        base_height = self._base.get_base_height(position)
        if height is not None:
            return base_height + height
        elif strict:
            return None
        else:
            return base_height

    def get_point_under(self, position: LPoint3d, strict: bool = False) -> LPoint3d | None:
        point_under = self._base.get_point_under(position)
        height = self.get_alt_under(point_under, strict)
        (tangent, binormal, normal) = self._base.get_tangent_plane_under(point_under)
        if height is not None:
            point_under += normal * height
        elif strict:
            point_under = None
        return point_under

    def get_tangent_plane_under(self, position: LPoint3d) -> tuple[LVector3d, LVector3d, LVector3d]:
        return self._base.get_tangent_plane_under(position)

    def _get_mesh_height_uv(self, patch_data, u, v, patch):
        """Bilinear interpolation of heightmap values at (u, v) within *patch*."""
        density = patch.density
        x = u * density
        y = v * density
        x0 = floor(x) / density * patch_data.width
        y0 = floor(y) / density * patch_data.height
        x1 = ceil(x) / density * patch_data.width
        y1 = ceil(y) / density * patch_data.height
        dx = u * patch_data.width - x0
        if x1 != x0:
            dx /= x1 - x0
        dy = v * patch_data.height - y0
        if y1 != y0:
            dy /= y1 - y0
        h_00 = patch_data.get_height(x0, y0, patch)
        h_01 = patch_data.get_height(x0, y1, patch)
        h_10 = patch_data.get_height(x1, y0, patch)
        h_11 = patch_data.get_height(x1, y1, patch)
        return h_00 + (h_10 - h_00) * dx + (h_01 - h_00) * dy + (h_00 + h_11 - h_01 - h_10) * dx * dy

    def get_height_patch(self, patch, u, v, strict=False):
        patch_data = self.heightmap.get_patch_data(patch, strict=strict)
        if patch_data is not None and patch_data.data_ready:
            h = self._get_mesh_height_uv(patch_data, u, v, patch)
            height = h * self._height_scale
        elif strict:
            height = None
        else:
            height = 0
        return height

    # --- Radius queries ---

    @property
    def radius(self) -> float:
        return self._base.radius

    def get_min_radius(self) -> float:
        return self._base.get_min_radius() + self._height_scale * self.heightmap.min_height

    def get_max_radius(self) -> float:
        return self._base.get_max_radius() + self._height_scale * self.heightmap.max_height

    def get_average_radius(self) -> float:
        return self._base.get_average_radius()

    # --- Helpers for the heightmap wrapper ---

    def get_base_height(self, position: LPoint3d) -> float:
        return self._base.get_base_height(position)

    def position_to_parametric(self, position: LPoint3d) -> tuple[float, float]:
        return self._base.position_to_parametric(position)

    # --- Shape management ---

    def get_height_scale(self) -> float:
        return self._height_scale

    def configure_shape(self, shape) -> None:
        self._base.configure_shape(shape)

    def configure_with_surface(self, surface) -> None:
        self._shape = surface.shape
        surface.patch_sources.add_source(self.heightmap)
        if self.biome is not None:
            surface.patch_sources.add_source(self.biome)
        surface.shape.face_unique = True
        surface.shape.set_heightmap(self.heightmap)

    def get_shape_axes(self) -> LVector3d:
        return self._base.get_shape_axes()

    # --- Shadow handling ---

    def do_create_shadow_caster_for(self, light_source, surface):
        return self._base.do_create_shadow_caster_for(light_source, surface)

    def add_self_shadow(self, light_source, surface) -> None:
        self._base.add_self_shadow(light_source, surface)

    # --- Ellipsoid model handling ---

    def copy_extend(self, delta: float):
        if not isinstance(self._base, EllipsoidModelInterface):
            raise AttributeError(f"{self._base.__class__.__name__} does not derive from EllipsoidModelInterface.")
        return self._base.copy_extend(delta)

    def get_radius_under(self, position: LPoint3d) -> float:
        if not isinstance(self._base, EllipsoidModelInterface):
            raise AttributeError(f"{self._base.__class__.__name__} does not derive from EllipsoidModelInterface.")
        return self._base.get_radius_under(position)

    def geodetic_to_cartesian(self, long: float, lat: float, h: float) -> LPoint3d:
        if not isinstance(self._base, EllipsoidModelInterface):
            raise AttributeError(f"{self._base.__class__.__name__} does not derive from EllipsoidModelInterface.")
        return self._base.geodetic_to_cartesian(long, lat, h)

    def cartesian_to_geodetic(self, position: LPoint3d) -> tuple[float, float, float]:
        if not isinstance(self._base, EllipsoidModelInterface):
            raise AttributeError(f"{self._base.__class__.__name__} does not derive from EllipsoidModelInterface.")
        return self._base.cartesian_to_geodetic(position)

    def parametric_to_cartesian(self, x: float, y: float, h: float) -> LPoint3d:
        if not isinstance(self._base, EllipsoidModelInterface):
            raise AttributeError(f"{self._base.__class__.__name__} does not derive from EllipsoidModelInterface.")
        return self._base.parametric_to_cartesian(x, y, h)

    def cartesian_to_parametric(self, position: LPoint3d) -> tuple[float, float, float]:
        if not isinstance(self._base, EllipsoidModelInterface):
            raise AttributeError(f"{self._base.__class__.__name__} does not derive from EllipsoidModelInterface.")
        return self._base.cartesian_to_parametric(position)

    # --- Heightmap mutation ---

    def set_heightmap(self, heightmap) -> None:
        self.heightmap = heightmap
