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


from .base import MovementController


class KineticMovementController(MovementController):
    """
    Base class for kinetic (physics-based) movement controllers.
    These controllers support velocity-based movement but NOT direct position setting.
    """

    kinetic_mover = True

    def __init__(self, entity):
        """
        Initializes a kinetic movement controller.

        Args:
            entity: The entity being controlled (should have anchor, physics_node, etc.)
        """
        super().__init__(entity.anchor)
        self.entity = entity

    def set_speed_relative(self, speed):
        """
        Sets velocity in the local reference frame. This is the primary movement method for kinetic controllers.

        Args:
            speed: Velocity vector in local coordinates.
        """
        pass
