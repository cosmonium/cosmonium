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
Orbit configuration schemas.

Defines Pydantic models for various orbit types including:
- Fixed position orbits
- Elliptical orbits
- Orbit categories
"""

from __future__ import annotations

from typing import Literal, Optional, Union

from pydantic import Field

from .base import ConfigBase
from .types import Point3Field


class FixedOrbitConfig(ConfigBase):
    """Configuration for a fixed position orbit."""

    type: Literal['fixed'] = Field(default='fixed', description="Orbit type identifier")
    position: Optional[Point3Field] = Field(None, description="Fixed position coordinates [x, y, z]")
    ra: Optional[float] = Field(None, description="Right ascension in degrees")
    ra_units: Optional[str] = Field('Deg', description="Units for right ascension")
    de: Optional[float] = Field(None, description="Declination in degrees")
    de_units: Optional[str] = Field('Deg', description="Units for declination")
    distance: Optional[float] = Field(None, description="Distance from parent")
    distance_units: Optional[str] = Field('pc', description="Units for distance")
    longitude: Optional[float] = Field(None, description="Longitude in degrees")
    latitude: Optional[float] = Field(None, description="Latitude in degrees")
    global_: Optional[bool] = Field(True, description="Global position flag", alias='global')
    frame: Optional[Union[str, dict]] = Field(None, description="Reference frame")


class GlobalPositionConfig(ConfigBase):
    """Configuration for a global position orbit."""

    type: Literal['global'] = Field(default='global', description="Orbit type identifier")
    position: Optional[Point3Field] = Field(default_factory=lambda: [0, 0, 0], description="Global position [x, y, z]")
    position_units: Optional[str] = Field('pc', description="Units for position")
    frame: Optional[Union[str, dict]] = Field(None, description="Reference frame")


class EllipticOrbitConfig(ConfigBase):
    """Configuration for an elliptical orbit with full orbital elements."""

    type: Literal['elliptic'] = Field(default='elliptic', description="Orbit type identifier")

    # Primary orbital elements
    semi_major_axis: Optional[float] = Field(None, description="Semi-major axis")
    semi_major_axis_units: Optional[str] = Field('AU', description="Units for semi-major axis")

    pericenter_distance: Optional[float] = Field(None, description="Pericenter distance")
    pericenter_distance_units: Optional[str] = Field('AU', description="Units for pericenter distance")

    period: Optional[float] = Field(None, description="Orbital period")
    period_units: Optional[str] = Field('Year', description="Units for period")

    mean_motion: Optional[float] = Field(None, description="Mean motion")
    mean_motion_units: Optional[str] = Field('deg/day', description="Units for mean motion")

    eccentricity: Optional[float] = Field(0.0, description="Orbital eccentricity")

    # Angular elements
    inclination: Optional[float] = Field(0.0, description="Orbital inclination in degrees")
    ascending_node: Optional[float] = Field(0.0, description="Longitude of ascending node in degrees")
    arg_of_periapsis: Optional[float] = Field(None, description="Argument of periapsis in degrees")
    long_of_pericenter: Optional[float] = Field(None, description="Longitude of pericenter in degrees")

    # Position at epoch
    mean_anomaly: Optional[float] = Field(None, description="Mean anomaly at epoch in degrees")
    mean_longitude: Optional[float] = Field(0.0, description="Mean longitude at epoch in degrees")
    time_of_perihelion: Optional[float] = Field(None, description="Time of perihelion passage")

    # Reference frame and time
    epoch: Optional[float] = Field(None, description="Epoch for orbital elements (J2000 time)")
    frame: Optional[Union[str, dict]] = Field(None, description="Reference frame")


class OrbitCategoryConfig(ConfigBase):
    """Configuration for orbit categories (for organizing named orbits)."""

    type: Literal['orbit-category'] = Field(default='orbit-category', description="Category type identifier")
    name: str = Field(..., description="Category name")
    description: Optional[str] = Field(None, description="Category description")
