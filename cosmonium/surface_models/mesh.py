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

from panda3d.core import LPoint3d, LVector3d

from ..shadows.shadowmap import CustomShadowMapShadowCaster
from .base import SurfaceModelInterface


class MeshSurfaceModel(SurfaceModelInterface):
    """Surface model for mesh-based arbitrary geometry."""

    def __init__(self, shape=None):
        # A reference to the shape is needed to implement get_height_patch and
        # get_height_under, which delegate to the shape's own methods.
        self._shape = shape

    def is_flat(self) -> bool:
        return False

    def is_spherical(self) -> bool:
        return False

    def get_alt_under(self, position: LPoint3d, strict: bool = False) -> float | None:
        return 0

    def get_height_under(self, position: LPoint3d, strict: bool = False) -> float | None:
        # TODO: This should be properly implemented.
        return self._shape.radius if self._shape is not None else 0

    def get_point_under(self, position: LPoint3d, strict: bool = False) -> LPoint3d | None:
        return LPoint3d()

    def get_tangent_plane_under(self, position: LPoint3d) -> tuple[LVector3d, LVector3d, LVector3d]:
        normal = position.normalized()
        if normal.dot(LVector3d.right()) != 0:
            tangent = LVector3d.right() * normal.dot(LVector3d.right())
            tangent.normalize()
            binormal = tangent.cross(normal)
        else:
            tangent = LVector3d.forward() * normal.dot(LVector3d.forward())
            tangent.normalize()
            binormal = tangent.cross(normal)
        return (tangent, binormal, normal)

    def get_height_patch(self, patch, u, v, strict=False):
        if self._shape is not None:
            return self._shape.get_height_patch(patch, u, v)
        return 0

    def get_min_radius(self) -> float:
        return 0

    def get_max_radius(self) -> float:
        return 0

    def get_average_radius(self) -> float:
        return 0

    def position_to_parametric(self, position: LPoint3d) -> tuple[float, float]:
        # TODO: Is it ever used ?
        return (position[0], position[1])

    def do_create_shadow_caster_for(self, light_source, surface):
        shadow_caster = CustomShadowMapShadowCaster(light_source, surface.body, surface)
        shadow_caster.add_target(surface, self_shadow=True)
        return shadow_caster

    def add_self_shadow(self, light_source, surface) -> None:
        if surface.instance_ready:
            surface.create_shadow_caster_for(light_source)
            surface.shadow_casters[light_source.source].add_target(surface, self_shadow=True)
