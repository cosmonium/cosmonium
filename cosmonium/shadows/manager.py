#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2025 Laurent Deru.
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

"""Shadow management classes.

This module provides shadow management systems that coordinate multiple
shadow casters and handle shader configuration for different shadow types.
"""

from __future__ import annotations

from ..shaders.shadows.ellipsoid import ShaderSphereShadow

from .base import ShadowBase
from .sphere import SphereShadowDataSource


class RingsShadows(ShadowBase):
    """Manages ring shadow casters for a target.

    Coordinates multiple ring shadow casters and integrates them with
    the shader system.
    """

    def __init__(self, target: object) -> None:
        """Initialize ring shadows manager.

        :param target: Target object that will receive ring shadows
        """
        self.target = target
        self.casters: list[object] = []
        self.old_casters: list[object] = []
        self.shader_components: dict[object, object] = {}
        self.data_sources: dict[object, object] = {}
        self.rebuild_needed: bool = False
        self.nb_updates: int = 0

    def add_shadow_caster(self, caster: object) -> None:
        """Add a ring shadow caster.

        :param caster: Ring shadow caster to add
        """
        if not caster.is_valid():
            return
        self.casters.append(caster)
        if caster not in self.old_casters:
            print("Add ring shadow caster", caster.name, "on", self.target.owner.get_friendly_name())
            shadow_shader = caster.create_shader_component()
            self.shader_components[caster] = shadow_shader
            data_source = caster.create_data_source()
            self.target.sources.add_source(data_source)
            self.data_sources[caster] = data_source
            self.target.shader.add_shadows(shadow_shader)
            self.rebuild_needed = True
        else:
            self.old_casters.remove(caster)

    def clear_shadows(self) -> None:
        """Clear all ring shadow casters."""
        for caster in self.casters:
            data_source = self.data_sources[caster]
            self.target.sources.remove_source(data_source)
        self.casters = []
        self.shader_components = {}
        self.data_sources = {}

    def start_update(self) -> None:
        """Start shadow update cycle."""
        if self.nb_updates == 0:
            self.old_casters = self.casters
            self.casters = []
            self.rebuild_needed = False
        self.nb_updates += 1

    def end_update(self) -> bool:
        """End shadow update cycle.

        :return: True if rebuild is needed
        """
        self.nb_updates -= 1
        if self.nb_updates == 0:
            for caster in self.old_casters:
                print(
                    "Remove ring shadow caster",
                    caster.name,
                    "on",
                    self.target.owner.get_name(),
                    self.target.get_name() or '',
                )
                shadow_shader = self.shader_components[caster]
                self.target.shader.remove_shadows(self.target.shape, self.target.appearance, shadow_shader)
                del self.shader_components[caster]
                data_source = self.data_sources[caster]
                self.target.sources.remove_source(data_source)
                del self.data_sources[caster]
                self.rebuild_needed = True
            self.old_casters = []
        return self.rebuild_needed


class SphereShadows(ShadowBase):
    """Manages sphere shadow casters for a target.

    Coordinates multiple sphere (analytic) shadow casters using a single
    shader component that can handle multiple occluders.
    """

    def __init__(self, target: object) -> None:
        """Initialize sphere shadows manager.

        :param target: Target object that will receive sphere shadows
        """

        self.target = target
        self.shadow_casters: list[object] = []
        self.max_occluders: int = 4
        self.far_sun: bool = False
        self.oblate_occluder: bool = True
        self.shader_component = ShaderSphereShadow(self.max_occluders, self.far_sun, self.oblate_occluder)
        self.data_source = SphereShadowDataSource(self, self.max_occluders, self.far_sun, self.oblate_occluder)
        self.nb_updates: int = 0

    def add_shadow_caster(self, shadow_caster: object) -> None:
        """Add a sphere shadow caster.

        :param shadow_caster: Sphere shadow caster to add
        """
        if shadow_caster not in self.shadow_casters:
            self.shadow_casters.append(shadow_caster)

    def empty(self) -> bool:
        """Check if there are no shadow casters.

        :return: True if no casters present
        """
        return len(self.shadow_casters) == 0

    def clear_shadows(self) -> None:
        """Clear all sphere shadow casters."""
        if len(self.shadow_casters) > 0:
            self.target.sources.remove_source(self.data_source)
        self.shadow_casters = []

    def start_update(self) -> None:
        """Start shadow update cycle."""
        if self.nb_updates == 0:
            self.had_sphere_occluder = not self.empty()
            self.shadow_casters = []
            self.rebuild_needed = False
        self.nb_updates += 1

    def end_update(self) -> bool:
        """End shadow update cycle.

        :return: True if rebuild is needed
        """
        self.nb_updates -= 1
        if self.nb_updates == 0:
            if self.empty() and self.had_sphere_occluder:
                print("Remove sphere shadow component on", self.target.owner.get_friendly_name())
                self.target.shader.remove_shadows(self.target.shape, self.target.appearance, self.shader_component)
                self.target.sources.remove_source(self.data_source)
                self.rebuild_needed = True
            elif not self.had_sphere_occluder and not self.empty():
                self.target.shader.add_shadows(self.shader_component)
                self.target.sources.add_source(self.data_source)
                print("Add sphere shadow component on", self.target.owner.get_friendly_name())
                self.rebuild_needed = True
        return self.rebuild_needed


class ShadowMapShadows(ShadowBase):
    """Manages shadow map casters for a target.

    Coordinates multiple shadow map casters and integrates them with
    the shader system.
    """

    def __init__(self, target: object) -> None:
        """Initialize shadow map shadows manager.

        :param target: Target object that will receive shadow map shadows
        """
        self.target = target
        self.casters: list[object] = []
        self.old_casters: list[object] = []
        self.shader_components: dict[object, object] = {}
        self.data_sources: dict[object, object] = {}
        self.rebuild_needed: bool = False
        self.nb_updates: int = 0

    def add_shadow_caster(self, caster: object, self_shadow: bool) -> None:
        """Add a shadow map caster.

        :param caster: Shadow map caster to add
        :param self_shadow: Enable self-shadowing
        """
        if not caster.is_valid():
            return
        self.casters.append(caster)
        if caster not in self.old_casters:
            print("Add shadow caster", caster.name, "on", self.target.owner.get_friendly_name())
            shadow_shader = caster.create_shader_component(self_shadow)
            self.shader_components[caster] = shadow_shader
            data_source = caster.create_data_source(self_shadow)
            self.target.sources.add_source(data_source)
            self.data_sources[caster] = data_source
            self.target.shader.add_shadows(shadow_shader)
            self.rebuild_needed = True
        else:
            self.old_casters.remove(caster)

    def clear_shadows(self) -> None:
        """Clear all shadow map casters."""
        for caster in self.casters:
            data_source = self.data_sources[caster]
            self.target.sources.remove_source(data_source)
        self.casters = []
        self.shader_components = {}
        self.data_sources = {}

    def start_update(self) -> None:
        """Start shadow update cycle."""
        if self.nb_updates == 0:
            self.old_casters = self.casters
            self.casters = []
            self.rebuild_needed = False
        self.nb_updates += 1

    def end_update(self) -> bool:
        """End shadow update cycle.

        :return: True if rebuild is needed
        """
        self.nb_updates -= 1
        if self.nb_updates == 0:
            for caster in self.old_casters:
                print(
                    "Remove shadow caster",
                    caster.name,
                    "on",
                    self.target.owner.get_name(),
                    self.target.get_name() or '',
                )
                shadow_shader = self.shader_components[caster]
                self.target.shader.remove_shadows(self.target.shape, self.target.appearance, shadow_shader)
                del self.shader_components[caster]
                data_source = self.data_sources[caster]
                self.target.sources.remove_source(data_source)
                del self.data_sources[caster]
                self.rebuild_needed = True
            self.old_casters = []
        return self.rebuild_needed


class MultiShadows(ShadowBase):
    """Manages multiple types of shadows for a target.

    Coordinates ring shadows, sphere shadows, and shadow map shadows,
    providing a unified interface for shadow management.
    """

    def __init__(self, target: object) -> None:
        """Initialize multi-shadow manager.

        :param target: Target object that will receive all shadow types
        """
        self.target = target
        self.rings_shadows = RingsShadows(target)
        self.sphere_shadows = SphereShadows(target)
        self.shadow_map_shadows = ShadowMapShadows(target)
        self.rebuild_needed: bool = False
        self.nb_updates: int = 0

    def clear_shadows(self) -> None:
        """Clear all shadow types."""
        self.rings_shadows.clear_shadows()
        self.sphere_shadows.clear_shadows()
        self.shadow_map_shadows.clear_shadows()
        self.target.shader.remove_all_shadows(self.target.shape, self.target.appearance)
        self.rebuild_needed = True

    def start_update(self) -> None:
        """Start shadow update cycle for all shadow types."""
        if self.nb_updates == 0:
            self.rings_shadows.start_update()
            self.sphere_shadows.start_update()
            self.shadow_map_shadows.start_update()
        self.nb_updates += 1

    def end_update(self) -> None:
        """End shadow update cycle for all shadow types."""
        self.nb_updates -= 1
        if self.nb_updates == 0:
            rings_shadows_rebuild_needed = self.rings_shadows.end_update()
            shadow_map_rebuild_needed = self.shadow_map_shadows.end_update()
            sphere_shadows_rebuild_needed = self.sphere_shadows.end_update()
            self.rebuild_needed = (
                rings_shadows_rebuild_needed or shadow_map_rebuild_needed or sphere_shadows_rebuild_needed
            )

    def add_ring_shadow_caster(self, shadow_caster: object) -> None:
        """Add a ring shadow caster.

        :param shadow_caster: Ring shadow caster to add
        """
        self.rings_shadows.add_shadow_caster(shadow_caster)

    def add_sphere_shadow_caster(self, shadow_caster: object) -> None:
        """Add a sphere shadow caster.

        :param shadow_caster: Sphere shadow caster to add
        """
        self.sphere_shadows.add_shadow_caster(shadow_caster)

    def add_shadow_map_shadow_caster(self, shadow_caster: object, self_shadow: bool) -> None:
        """Add a shadow map caster.

        :param shadow_caster: Shadow map caster to add
        :param self_shadow: Enable self-shadowing
        """
        self.shadow_map_shadows.add_shadow_caster(shadow_caster, self_shadow)
