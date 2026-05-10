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

from abc import ABC, abstractmethod

from panda3d.core import LPoint3d, LVector3d


class SurfaceModelInterface(ABC):
    """
    Abstract interface for surface geometry models.

    A surface model defines the geometric behaviour of a surface, providing methods
    to compute heights, altitudes, and tangent planes at any point, independent of
    the rendering shape and appearance.
    """

    # --- Geometry predicates ---

    @abstractmethod
    def is_flat(self) -> bool:
        """Returns True if the surface has no height variation (altitude is always 0)."""
        ...

    @abstractmethod
    def is_spherical(self) -> bool:
        """Returns True if the surface is spherical/ellipsoidal."""
        ...

    # --- Surface geometry queries ---

    @abstractmethod
    def get_alt_under(self, position: LPoint3d, strict: bool = False) -> float | None:
        """
        Returns the altitude above the base surface below the given position.
        Returns None if not found and strict is True, or 0 if strict is False.
        """
        ...

    @abstractmethod
    def get_height_under(self, position: LPoint3d, strict: bool = False) -> float | None:
        """
        Returns the total height (distance from centre) at the given position.
        Returns None if not found and strict is True or base height if strict is False.
        """
        ...

    @abstractmethod
    def get_point_under(self, position: LPoint3d, strict: bool = False) -> LPoint3d | None:
        """
        Return the surface point closest to the given position.

        Args:
            position: The position expressed as cartesian body-centred coordinates (ECEF).
            strict: If True, returns None if no surface point is found below the position.
        Returns:
            Returns the surface point below the given position.
            Returns None if not found and strict is True, or the point on the base surface is strict is False.
        """
        ...

    @abstractmethod
    def get_tangent_plane_under(self, position: LPoint3d) -> tuple[LVector3d, LVector3d, LVector3d]:
        """Returns (tangent, binormal, normal) of the surface below the given position."""
        ...

    @abstractmethod
    def get_height_patch(self, patch, u, v, strict=False):
        """Returns the height at the given patch UV coordinates."""
        ...

    # --- Radius queries (only for spherical models) ---

    @abstractmethod
    def get_min_radius(self) -> float:
        """Returns the minimum radius/height of the surface."""
        ...

    @abstractmethod
    def get_max_radius(self) -> float:
        """Returns the maximum radius/height of the surface."""
        ...

    @abstractmethod
    def get_average_radius(self) -> float:
        """Returns the average radius of the surface."""
        ...

    # --- Helpers for the heightmap wrapper ---

    def get_base_height(self, position: LPoint3d) -> float:
        """Returns the base (pre-heightmap) height at the given position."""
        return 0.0

    @abstractmethod
    def position_to_parametric(self, position: LPoint3d) -> tuple[float, float]:
        """
        Converts a 3D position to 2D parametric (x, y) coordinates used for patch
        lookup.
        """
        ...

    # --- Shape management ---

    def get_height_scale(self) -> float:
        """
        Returns the height scale used by the patched-shape renderer.
        TODO: this is a workaround; should be removed once patchedshape is fixed.
        """
        return 1.0

    def configure_shape(self, shape) -> None:
        """Configures the geometric shape object associated with this surface model."""
        pass

    def configure_with_surface(self, surface) -> None:
        """
        Called by Surface after it is fully initialised.
        Allows the model to register data sources, configure the shape, etc.
        """
        pass

    def get_shape_axes(self) -> LVector3d:
        """Returns the shape axes of the surface (used for ellipsoid-aware rendering)."""
        return LVector3d(1.0, 1.0, 1.0)

    # --- Shadow handling ---

    def do_create_shadow_caster_for(self, light_source, surface):
        """Creates and returns a shadow caster for the given light source, or None."""
        return None

    def add_self_shadow(self, light_source, surface) -> None:
        """Registers self-shadowing for the given light source."""
        pass
