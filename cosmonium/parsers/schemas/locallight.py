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
Local light configuration schemas.

Defines Pydantic models for local light sources including directional,
point, and spot lights, along with their shadow configurations.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import Field

from .base import ConfigBase
from .types import ColorField, Point3Field, Vector3Field


class ShadowsConfig(ConfigBase):
    """Configuration for shadow casting by a local light."""

    near: float = Field(0.0, description="Near clipping plane for shadow map")
    far: float = Field(100.0, description="Far clipping plane for shadow map")
    width: Optional[float] = Field(None, description="Shadow map film width (directional lights only)")
    height: Optional[float] = Field(None, description="Shadow map film height (directional lights only)")


class LocalDirectionalLightConfig(ConfigBase):
    """Configuration for a local directional light source."""

    type: Literal['directional'] = Field(default='directional', description="Light type identifier")
    name: Optional[str] = Field(None, description="Light name")
    disabled: bool = Field(False, description="Whether this light is disabled")
    position: Optional[Point3Field] = Field([0, 0, 0], description="Light position [x, y, z]")
    color: Optional[ColorField] = Field([1, 1, 1, 1], description="Light color [r, g, b] or [r, g, b, a]")
    power: float = Field(1.0, description="Light power multiplier")
    direction: Optional[Vector3Field] = Field([0, 1, 0], description="Light direction [x, y, z]")
    shadows: Optional[ShadowsConfig] = Field(None, description="Shadow casting configuration")


class LocalPointLightConfig(ConfigBase):
    """Configuration for a local point light source."""

    type: Literal['point'] = Field(default='point', description="Light type identifier")
    name: Optional[str] = Field(None, description="Light name")
    disabled: bool = Field(False, description="Whether this light is disabled")
    position: Optional[Point3Field] = Field([0, 0, 0], description="Light position [x, y, z]")
    color: Optional[ColorField] = Field([1, 1, 1, 1], description="Light color [r, g, b] or [r, g, b, a]")
    power: float = Field(1.0, description="Light power multiplier")
    attenuation: Optional[Vector3Field] = Field(
        [1, 0, 1], description="Attenuation coefficients [constant, linear, quadratic]"
    )
    max_distance: float = Field(1.0, description="Maximum effective distance of the light")


class LocalSpotLightConfig(ConfigBase):
    """Configuration for a local spot light source."""

    type: Literal['spot'] = Field(default='spot', description="Light type identifier")
    name: Optional[str] = Field(None, description="Light name")
    disabled: bool = Field(False, description="Whether this light is disabled")
    position: Optional[Point3Field] = Field([0, 0, 0], description="Light position [x, y, z]")
    color: Optional[ColorField] = Field([1, 1, 1, 1], description="Light color [r, g, b] or [r, g, b, a]")
    power: float = Field(1.0, description="Light power multiplier")
    attenuation: Optional[Vector3Field] = Field(
        [1, 0, 1], description="Attenuation coefficients [constant, linear, quadratic]"
    )
    max_distance: float = Field(1.0, description="Maximum effective distance of the light")
    inner_cone: float = Field(0.0, description="Inner cone angle in degrees")
    outer_cone: float = Field(45.0, description="Outer cone angle in degrees")
    exponent: Optional[float] = Field(None, description="Spotlight exponent (falloff)")
    direction: Optional[Vector3Field] = Field([0, 1, 0], description="Spotlight direction [x, y, z]")
    shadows: Optional[ShadowsConfig] = Field(None, description="Shadow casting configuration")
