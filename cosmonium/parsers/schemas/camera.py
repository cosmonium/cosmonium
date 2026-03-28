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
Camera controller configuration schemas.

Defines Pydantic models for camera controller types.
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import Field

from .base import ConfigBase


class SurfaceFollowCameraConfig(ConfigBase):
    """Configuration for a surface-following camera controller."""

    type: Literal['surface-follow'] = Field(default='surface-follow', description="Camera controller type")
    distance: float = Field(5.0, description="Follow distance from the surface")
    max_: float = Field(1.5, description="Maximum scale factor", alias='max')


class FixedCameraConfig(ConfigBase):
    """Configuration for a fixed-position camera controller."""

    type: Literal['fixed'] = Field(default='fixed', description="Camera controller type")
    position: Optional[List[float]] = Field(None, description="Fixed camera position [x, y, z]")
