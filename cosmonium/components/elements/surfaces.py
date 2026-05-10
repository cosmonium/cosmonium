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

from typing import TYPE_CHECKING

from panda3d.core import LQuaternion

from ...entities.entity import Entity

if TYPE_CHECKING:
    from ...surface_models import SurfaceModelInterface


class Surface(Entity):
    """
    Surface component representing the surface of a celestial body.

    Provides methods to query altitude, height, surface points and tangent planes
    at arbitrary positions by delegating to a composable *model* object that
    implements :class:`SurfaceModelInterface`.

    Shadow-caster creation and self-shadow registration are also delegated to the
    model, so the concrete model class determines the appropriate shadow strategy.
    """

    def __init__(
        self,
        name=None,
        category=None,
        resolution=None,
        attribution=None,
        model: SurfaceModelInterface = None,
        shape=None,
        appearance=None,
        shader=None,
        clickable=True,
    ):
        Entity.__init__(self, name, shape, appearance, shader, clickable)
        self.category = category
        self.resolution = resolution
        self.attribution = attribution
        self.body = None
        self.model = model
        if model is not None:
            # TODO: height_scale is a workaround for patchedshape scale; should be removed.
            self.height_scale = model.get_height_scale()
            model.configure_with_surface(self)
        else:
            self.height_scale = 1.0

    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Surface configuration

    def get_component_name(self):
        """Returns a human-readable name for this component, used in the UI and logs."""
        return _('Surface')

    def set_body(self, body):
        """Sets the body this surface is attached to."""
        self.body = body

    def configure_render_order(self):
        """Configures the render order for this surface."""
        self.instance.set_bin("front_to_back", 0)

    # ------------------------------------------------------------------
    # Model delegation
    # ------------------------------------------------------------------

    # --- Shape configuration ---

    def configure_shape(self):
        """Configures the geometric shape according to the surface model."""
        if self.model is not None:
            self.model.configure_shape(self.shape)

    # --- Geometry predicates ---

    def is_flat(self) -> bool:
        if self.model is not None:
            return self.model.is_flat()
        return True

    def is_spherical(self) -> bool:
        if self.model is not None:
            return self.model.is_spherical()
        return self.shape.is_spherical()

    # --- Surface geometry queries ---

    def get_alt_under(self, position, strict=False):
        """
        Returns the altitude above the base surface below *position*.
        Returns ``None`` if not found and *strict* is ``True``, or ``0`` otherwise.
        """
        return self.model.get_alt_under(position, strict)

    def get_height_under(self, position, strict=False):
        """
        Returns the total height (distance from the centre) at *position*.
        Returns ``None`` if not found and *strict* is ``True``.
        """
        return self.model.get_height_under(position, strict)

    def get_point_under(self, position, strict=False):
        """
        Returns the surface point below *position*.
        Returns ``None`` if not found and *strict* is ``True``.
        """
        return self.model.get_point_under(position, strict)

    def get_tangent_plane_under(self, position):
        """Returns ``(tangent, binormal, normal)`` of the surface below *position*."""
        return self.model.get_tangent_plane_under(position)

    def get_height_patch(self, patch, u, v):
        """Returns the surface height at the given patch UV coordinates."""
        return self.model.get_height_patch(patch, u, v)

    # --- Radius queries (only for spherical models) ---

    def get_min_radius(self):
        return self.model.get_min_radius()

    def get_max_radius(self):
        return self.model.get_max_radius()

    def get_average_radius(self):
        return self.model.get_average_radius()

    def get_shape_axes(self):
        return self.model.get_shape_axes()

    # --- Shape helpers ---

    def parametric_to_shape_coord(self, x, y):
        """Returns the shape coordinates corresponding to the given parametric coordinates."""
        return self.shape.parametric_to_shape_coord(x, y)

    # --- Shadow handling ---

    def do_create_shadow_caster_for(self, light_source):
        if self.model is not None:
            return self.model.do_create_shadow_caster_for(light_source, self)
        return None

    def add_self_shadow(self, light_source):
        if self.model is not None:
            self.model.add_self_shadow(light_source, self)

    # ------------------------------------------------------------------
    # Frame update
    # ------------------------------------------------------------------

    def update_instance(self, scene_manager, camera_pos, camera_rot):
        """Updates the instance of this surface, called every frame."""
        Entity.update_instance(self, scene_manager, camera_pos, camera_rot)
        if not self.instance_ready:
            return
        self.instance.set_quat(LQuaternion(*self.body.anchor.get_absolute_orientation()))
