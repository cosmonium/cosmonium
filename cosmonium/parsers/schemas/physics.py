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


"""
Physics shape configuration schemas.

Defines Pydantic models for physics collision shapes used by both
the Bullet physics engine and Panda3D's built-in collision system.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from .base import ConfigBase


class BulletCapsuleShapeConfig(ConfigBase):
    """Configuration for a Bullet physics capsule collision shape."""

    type: Literal['capsule'] = Field(default='capsule', description="Shape type identifier")
    width: float = Field(0.5, description="Capsule radius")
    height: float = Field(1.8, description="Total capsule height (including end caps)")


class CollisionCapsuleShapeConfig(ConfigBase):
    """Configuration for a Panda3D collision capsule shape."""

    type: Literal['capsule'] = Field(default='capsule', description="Shape type identifier")
    width: float = Field(0.5, description="Capsule radius")
    height: float = Field(1.8, description="Total capsule height")
