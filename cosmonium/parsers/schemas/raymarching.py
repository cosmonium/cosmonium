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


"""Raymarching appearance configuration schemas."""

from __future__ import annotations

from typing import Any, List, Literal, Optional

from pydantic import Field

from .base import ConfigBase


class VolumetricDensityRayMarchingConfig(ConfigBase):
    """Configuration for volumetric density ray marching appearance."""

    type: Literal['raymarching:density'] = 'raymarching:density'
    density: Optional[Any] = Field(None, description="Density noise function")
    absorption_factor: float = Field(0.00001, description="Absorption factor")
    absorption_coef: List[float] = Field(
        default_factory=lambda: [1, 1, 1], description="Absorption coefficients [r, g, b]"
    )
    mie_coef: float = Field(0.1, description="Mie scattering coefficient")
    phase_coef: float = Field(0, description="Phase coefficient")
    source_color: List[float] = Field(default_factory=lambda: [1, 1, 1], description="Source light color [r, g, b]")
    source_power: float = Field(10000.0, description="Source light power")
    emission_power: float = Field(0.0, description="Emission power")
    emission_color: List[float] = Field(default_factory=lambda: [1, 1, 1], description="Emission color [r, g, b]")
    max_steps: int = Field(16, description="Maximum ray marching steps")
    hdr: bool = Field(False, description="Enable HDR rendering")
    exposure: float = Field(4.0, description="HDR exposure")


class VolumetricDensityEmissiveRayMarchingConfig(ConfigBase):
    """Configuration for volumetric density emissive ray marching appearance."""

    type: Literal['raymarching:emissive'] = 'raymarching:emissive'
    density: Optional[Any] = Field(None, description="Density noise function")
    emission_power: float = Field(0.0, description="Emission power")
    emission_color: List[float] = Field(default_factory=lambda: [1, 1, 1], description="Emission color [r, g, b]")
    max_steps: int = Field(16, description="Maximum ray marching steps")
    hdr: bool = Field(False, description="Enable HDR rendering")
    exposure: float = Field(4.0, description="HDR exposure")


class BulgeRayMarchingConfig(ConfigBase):
    """Configuration for galactic bulge ray marching appearance."""

    type: Literal['raymarching:bulge'] = 'raymarching:bulge'
    effective_intensity: float = Field(1.0, description="Effective intensity of the bulge")
    effective_radius: float = Field(1.0, description="Effective radius of the bulge")
    emissive_color: List[float] = Field(default_factory=lambda: [1, 1, 1], description="Emissive color [r, g, b]")
    emissive_scale: float = Field(1.0, description="Emissive scale factor")
    max_steps: int = Field(16, description="Maximum ray marching steps")
    hdr: bool = Field(False, description="Enable HDR rendering")
    exposure: float = Field(4.0, description="HDR exposure")


class SDFRayMarchingConfig(ConfigBase):
    """Configuration for SDF (Signed Distance Field) ray marching appearance."""

    type: Literal['raymarching:sdf'] = 'raymarching:sdf'
    shape: Any = Field('sphere', description="SDF shape (noise parser input)")
    max_steps: int = Field(16, description="Maximum ray marching steps")
    hdr: bool = Field(False, description="Enable HDR rendering")
    exposure: float = Field(4.0, description="HDR exposure")


class SDFPointShapeConfig(ConfigBase):
    """Configuration for a point SDF shape."""

    name: Optional[str] = Field(None, description="Dynamic parameter name")
    position: List[float] = Field(default_factory=lambda: [0, 0, 0], description="Point position [x, y, z]")


class SDFSphereShapeConfig(ConfigBase):
    """Configuration for a sphere SDF shape."""

    name: Optional[str] = Field(None, description="Dynamic parameter name")
    position: List[float] = Field(default_factory=lambda: [0, 0, 0], description="Sphere center [x, y, z]")
    radius: float = Field(1.0, description="Sphere radius")
    radius_range: List[float] = Field(
        default_factory=lambda: [0.0, 1.0], description="Radius animation range [min, max]"
    )
