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

"""Base classes and interfaces for shadow system.

This module provides abstract base classes and interfaces that define
the common structure for different shadow implementations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..entities.entity import Entity


class ShadowCasterBase:
    """Abstract base class for shadow casters.

    Shadow casters generate shadows from light sources, either using
    analytic methods or shadow maps.
    """

    def __init__(self, light: object) -> None:
        """Initialize shadow caster with a light source.

        Args:
            light: The light source that will cast shadows.
        """
        self.light = light

    def is_analytic(self) -> bool:
        """Check if this shadow caster uses analytic shadow calculation.

        Returns:
            True if analytic, False if using shadow maps.
        """
        pass

    def create(self) -> None:
        """Create and initialize shadow resources."""
        pass

    def remove(self) -> None:
        """Remove and cleanup shadow resources."""
        pass

    def check_settings(self) -> None:
        """Check and apply current shadow settings."""
        pass

    def is_valid(self) -> bool:
        """Check if shadow caster is properly initialized and valid.

        Returns:
            True if valid and ready to use.
        """
        return True

    def add_target(self, entity: 'Entity') -> None:
        """Add an entity as a target for this shadow caster.

        Args:
            entity: Entity that will receive shadows.
        """
        pass

    def update(self, scene_manager: object) -> None:
        """Update shadow caster state for current frame.

        Args:
            scene_manager: The scene manager.
        """
        pass


class ShadowBase:
    """Abstract base class for shadow management systems.

    Shadow management systems coordinate multiple shadow casters and
    handle shader configuration for rendering shadows.
    """

    pass
