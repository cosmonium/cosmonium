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
Galaxies configuration schemas.

Defines Pydantic models for galaxy configurations.
"""

from __future__ import annotations

from typing import Any, List, Literal, Optional

from pydantic import Field

from .base import ConfigBase
from .stellarobjects import StellarObjectConfig
from .types import DistanceLyField, Point3Field, Vector3Field


class GalaxyAppearanceConfig(ConfigBase):
    """Configuration for galaxy appearance (sprite and scale)."""

    sprite: Optional[str] = Field('exp', description="Sprite type: 'gaussian', 'exp', 'round'")
    scale: Optional[float] = Field(5.0, description="Color scale")


class LenticularGalaxyShapeConfig(ConfigBase):
    """Configuration for lenticular galaxy shape."""

    shape: Literal['lenticular'] = 'lenticular'
    nb_points_bulge: int = Field(200, description="Number of bulge points")
    nb_points_arms: int = Field(1000, description="Number of arm points")
    sersic_bulge: float = Field(4.0, description="Bulge Sersic index")
    sersic: float = Field(1.0, description="Disk Sersic index")
    winding: float = Field(360, description="Winding angle in degrees")
    spread: float = Field(0.4, description="Point spread")
    zspread: float = Field(0.1, description="Z-axis spread")
    size: int = Field(200, description="Point size")


class EllipticalGalaxyShapeConfig(ConfigBase):
    """Configuration for elliptical galaxy shape."""

    shape: Literal['elliptical'] = 'elliptical'
    factor: float = Field(0, description="Ellipticity factor (0=E0, 7=E7)")
    nb_points: int = Field(1000, description="Number of points")
    sersic: float = Field(4.0, description="Sersic index")
    spread: float = Field(0.4, description="Point spread")
    zspread: float = Field(0.2, description="Z-axis spread")
    size: int = Field(200, description="Point size")


class IrregularGalaxyShapeConfig(ConfigBase):
    """Configuration for irregular galaxy shape."""

    shape: Literal['irregular'] = 'irregular'
    nb_points: int = Field(1000, description="Number of points")
    sersic: float = Field(4.0, description="Sersic index")
    spread: float = Field(0.2, description="Point spread")
    zspread: float = Field(0.1, description="Z-axis spread")
    size: int = Field(200, description="Point size")


class SpiralGalaxyShapeConfig(ConfigBase):
    """Configuration for spiral galaxy shape."""

    shape: Literal['spiral'] = 'spiral'
    pitch: Optional[float] = Field(None, description="Spiral pitch angle in radians")
    N: Optional[float] = Field(1.0, description="N parameter for FullSpiral")
    B: Optional[float] = Field(1.0, description="B parameter for FullSpiral")
    ring: bool = Field(False, description="Use ring spiral variant")
    nb_points_bulge: int = Field(400, description="Number of bulge points")
    nb_points_arms: int = Field(1000, description="Number of arm points")
    sersic_bulge: float = Field(4.0, description="Bulge Sersic index")
    sersic: float = Field(1.0, description="Disk Sersic index")
    winding: float = Field(360, description="Winding angle in degrees")
    spread: Optional[float] = Field(None, description="Point spread (defaults to pitch/5 if pitch set, else 0.1)")
    zspread: float = Field(0.02, description="Z-axis spread")
    size: int = Field(200, description="Sprite size")


class GalaxyConfig(StellarObjectConfig):
    """Configuration for galaxies (handle type field conflict with galaxy-type)."""

    type: Literal['galaxy'] = Field(default='galaxy', description="Object type")
    body_class: Optional[str] = Field('galaxy', description="Body classification")

    # Galaxy properties
    radius: Optional[DistanceLyField] = Field(None, description="Galaxy radius (float in ly, or [value, unit])")
    classification: Optional[str] = Field(None, description="Galaxy classification (spiral, elliptical, etc.)")
    magnitude: Optional[float] = Field(None, description="Absolute magnitude")
    shape: Optional[Any] = Field(None, description="Galaxy shape configuration")
    appearance: Optional[Any] = Field(None, description="Galaxy appearance configuration")

    # Position and scale
    position: Optional[Point3Field] = Field(None, description="Galaxy position")
    distance: Optional[float] = Field(None, description="Distance from observer")
    size: Optional[float] = Field(None, description="Galaxy size")
    scale: Optional[Vector3Field] = Field(None, description="Galaxy scale")

    # Hierarchical structure
    children: Optional[List[Any]] = Field(None, description="Child object configurations")
