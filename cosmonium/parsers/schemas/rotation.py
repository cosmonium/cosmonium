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
Rotation configuration schemas.

Defines Pydantic models for various rotation types including:
- Uniform rotation
- Fixed rotation
- Synchronous rotation
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import Field

from .base import ConfigBase
from .types import AngleDegField, TimeYearField, Vector3Field


class UniformRotationConfig(ConfigBase):
    """Configuration for uniform rotation."""

    type: Literal['uniform'] = Field(default='uniform', description="Rotation type identifier")

    # Rotation parameters
    period: Optional[TimeYearField] = Field(None, description="Rotation period (float in years, or [value, unit])")

    synchronous: Optional[bool] = Field(False, description="Whether rotation is synchronous with orbit")

    # Orientation parameters
    inclination: Optional[AngleDegField] = Field(
        0.0, description="Axial inclination (float in degrees, or [value, unit])"
    )
    ascending_node: Optional[AngleDegField] = Field(
        0.0, description="Ascending node (float in degrees, or [value, unit])"
    )

    ra: Optional[AngleDegField] = Field(
        None, description="Right ascension of north pole (float in degrees, or [value, unit])"
    )
    de: Optional[AngleDegField] = Field(
        0.0, description="Declination of north pole (float in degrees, or [value, unit])"
    )
    meridian: Optional[AngleDegField] = Field(
        0.0, description="Prime meridian angle at epoch (float in degrees, or [value, unit])"
    )

    # Reference frame and time
    epoch: Optional[float] = Field(None, description="Epoch for rotation parameters (J2000 time)")
    frame: Optional[str] = Field(None, description="Reference frame")


class FixedRotationConfig(ConfigBase):
    """Configuration for fixed rotation with axis and angle."""

    type: Literal['fixed'] = Field(default='fixed', description="Rotation type identifier")

    # Rotation axis and angle
    angle: Optional[float] = Field(None, description="Rotation angle in degrees")
    axis: Optional[Vector3Field] = Field(None, description="Rotation axis vector [x, y, z]")

    # Alternative: orientation parameters
    ra: Optional[AngleDegField] = Field(
        None, description="Right ascension of axis (float in degrees, or [value, unit])"
    )
    de: Optional[AngleDegField] = Field(None, description="Declination of axis (float in degrees, or [value, unit])")
    inclination: Optional[AngleDegField] = Field(
        None, description="Axial inclination (float in degrees, or [value, unit])"
    )
    ascending_node: Optional[AngleDegField] = Field(
        None, description="Ascending node (float in degrees, or [value, unit])"
    )

    # Reference frame
    frame: Optional[str] = Field(None, description="Reference frame")
