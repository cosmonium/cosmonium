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
Stellar body configuration schemas.

Defines Pydantic models for stars, planets, moons, systems, etc.
"""

from __future__ import annotations

from typing import Any, List, Literal, Optional, Union

from pydantic import Field

from .base import ConfigBase
from .types import ColorField, DistanceKmField, Vector3Field


class StarSurfaceFactoryConfig(ConfigBase):
    """Configuration for procedural star surface factory."""

    type: Literal['star-surface'] = Field(default='star-surface', description="Object type")
    name: Optional[str] = Field(None, description="Factory name")
    func: Optional[Any] = Field(None, description="Noise function configuration")
    noise: Optional[Any] = Field(None, description="Noise function (deprecated, use func)")
    size: int = Field(256, description="Texture size")


class StellarObjectConfig(ConfigBase):
    """Base configuration for stellar objects."""

    name: Union[str, List[str]] = Field(..., description="Object name(s)")
    parent: Optional[str] = Field(None, description="Parent object name")
    body_class: Optional[str] = Field(None, description="Body classification")
    point_color: Optional[ColorField] = Field(None, description="Point color [r, g, b] or [r, g, b, a]")

    # Motion - can be references (strings) or inline dicts
    orbit: Optional[Union[str, dict, Any]] = Field(None, description="Orbit configuration or reference")
    rotation: Optional[Union[str, dict, Any]] = Field(None, description="Rotation configuration or reference")
    frame: Optional[str] = Field(None, description="Reference frame")


class StellarBodyConfig(StellarObjectConfig):
    """Base configuration for stellar bodies (stars and reflective bodies)."""

    # Body properties
    radius: Optional[DistanceKmField] = Field(None, description="Body radius (float in km, or [value, unit])")
    diameter: Optional[DistanceKmField] = Field(None, description="Body diameter (float in km, or [value, unit])")
    ellipticity: Optional[float] = Field(None, description="Body oblateness/ellipticity")
    axes: Optional[Vector3Field] = Field(None, description="Body axes [a, b, c]")

    # Appearance
    surfaces: Optional[List[Union[str, dict, Any]]] = Field(None, description="Surface configurations")
    surface_factory: Optional[str] = Field(None, description="Procedural surface factory name")
    #
    appearance: Optional[Union[str, dict]] = Field(None, description="Appearance configuration or reference")
    shape: Optional[Union[str, dict]] = Field(None, description="Shape configuration or reference")

    # Additional features
    clouds: Optional[Any] = Field(None, description="Cloud configuration")
    atmosphere: Optional[Any] = Field(None, description="Atmosphere configuration")
    rings: Optional[Any] = Field(None, description="Ring configuration")


class StarConfig(StellarBodyConfig):
    """Configuration for stars."""

    type: Literal['star'] = Field(default='star', description="Object type")

    # Star properties
    temperature: Optional[float] = Field(None, description="Surface temperature in Kelvin")
    magnitude: Optional[float] = Field(None, description="Absolute magnitude")
    spectral_type: Optional[str] = Field(None, description="Spectral type")


class ReflectiveBodyConfig(StellarBodyConfig):
    """Configuration for planets."""

    type: Literal[
        'reflective',
        'planet',
        'dwarfplanet',
        'moon',
        'minormoon',
        'lostmoon',
        'asteroid',
        'comet',
        'interstellar',
        'spacecraft',
    ] = Field(default='reflective', description="Object type")

    # Planet properties
    albedo: Optional[float] = Field(0.5, description="Surface albedo")

    # Controller
    controller: Optional[Any] = Field(None, description="Controller configuration")


class StellarRingsConfig(StellarObjectConfig):
    """Configuration for stellar rings."""

    type: Literal['rings'] = Field(default='rings', description="Object type")

    # Ring properties
    inner_radius: DistanceKmField = Field(description="Inner radius of the rings")
    outer_radius: DistanceKmField = Field(description="Outer radius of the rings")
    lighting_model: Optional[Any] = Field(None, description="Lighting model configuration")
    appearance: Optional[Any] = Field(None, description="Appearance configuration")


class SystemConfig(StellarObjectConfig):
    """Configuration for hierarchical systems with children."""

    type: Literal['system', 'barycenter'] = Field(default='system', description="Object type")

    # System properties
    star_system: Optional[bool] = Field(False, description="Is this a star system")

    # Hierarchical structure
    children: Optional[List[Any]] = Field(None, description="Child object configurations")


class UniverseConfig(ConfigBase):
    """Configuration for root universe with children."""

    type: Literal['universe'] = Field(default='universe', description="Object type")

    # Hierarchical structure
    children: Optional[List[Any]] = Field(None, description="Child object configurations")


class NebulaConfig(StellarObjectConfig):
    """Configuration for nebulae."""

    type: Literal['nebula'] = Field(default='nebula', description="Object type")
    body_class: Optional[str] = Field('nebula', description="Body classification")

    # Nebula properties
    radius: Optional[DistanceKmField] = Field(None, description="Nebula radius (float in km, or [value, unit])")
    magnitude: Optional[float] = Field(None, description="Absolute magnitude")

    # Appearance
    surfaces: Optional[List[Union[str, dict, Any]]] = Field(None, description="Surface configurations")
    # Surface inline properties (when surfaces not provided)
    shape: Optional[Union[str, dict, Any]] = Field(None, description="Shape configuration")
    appearance: Optional[Union[str, dict, Any]] = Field(None, description="Appearance configuration")
