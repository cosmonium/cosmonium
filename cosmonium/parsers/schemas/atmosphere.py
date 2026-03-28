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
Atmosphere configuration schemas.

Defines Pydantic models for different atmosphere types.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from .base import ConfigBase
from .types import Vector3Field


class CelestiaAtmosphereConfig(ConfigBase):
    """Configuration for Celestia-style atmospheres."""

    type: Literal['celestia'] = 'celestia'
    height: Optional[float] = Field(None, description="Atmosphere height")
    mie: float = Field(0.0, description="Mie scattering coefficient")
    mie_scale_height: float = Field(0.0, description="Mie scale height")
    mie_asymmetry: float = Field(0.0, description="Mie phase asymmetry")
    rayleigh: Optional[Vector3Field] = Field(None, description="Rayleigh scattering coefficient [r, g, b]")
    rayleigh_scale_height: float = Field(0.0, description="Rayleigh scale height")
    absorption: Optional[Vector3Field] = Field(None, description="Absorption coefficient [r, g, b]")
    shape: Optional[Any] = Field(None, description="Atmosphere shape configuration")


class ONeilSimpleAtmosphereConfig(ConfigBase):
    """Configuration for simple O'Neil atmospheres."""

    type: Literal['oneil:simple'] = 'oneil:simple'
    shape: Optional[Any] = Field(None, description="Atmosphere shape configuration")
    height: Optional[float] = Field(None, description="Atmosphere height")
    rayleigh: Optional[float] = Field(0.0025, description="Rayleigh scattering coefficient")
    mie: Optional[float] = Field(0.0015, description="Mie scattering coefficient")
    g: Optional[float] = Field(-0.99, description="Mie phase asymmetry factor")
    sun_power: Optional[float] = Field(15.0, description="Sun power")
    samples: Optional[int] = Field(5, description="Number of samples")
    calc_in_fragment: Optional[bool] = Field(True, description="Calculate in fragment shader")
    normalize: Optional[bool] = Field(True, description="Normalize scattering result")
    hdr: Optional[bool] = Field(True, description="Enable HDR rendering")
    exposure: Optional[float] = Field(1, description="Exposure factor")
    atm_calc_in_fragment: Optional[bool] = Field(True, description="Atmosphere calculation in fragment shader")
    atm_normalize: Optional[bool] = Field(True, description="Atmosphere normalization")
    atm_hdr: Optional[bool] = Field(True, description="Atmosphere HDR")
    atm_exposure: Optional[float] = Field(0.8, description="Atmosphere exposure")


class ONeilAtmosphereConfig(ConfigBase):
    """Configuration for full O'Neil atmospheres."""

    type: Literal['oneil'] = 'oneil'
    shape: Optional[Any] = Field(None, description="Atmosphere shape configuration")
    height: Optional[float] = Field(160, description="Atmosphere height")
    rayleigh: Optional[float] = Field(0.0025, description="Rayleigh scattering coefficient")
    rayleigh_scale_depth: Optional[float] = Field(None, description="Rayleigh scale depth")
    rayleigh_absorption: Optional[Vector3Field] = Field([0, 0, 0], description="Rayleigh absorption [r, g, b]")
    mie_scale_depth: Optional[float] = Field(None, description="Mie scale depth")
    mie_alpha_coef: Optional[float] = Field(0, description="Mie alpha coefficient")
    mie_beta_coef: Optional[float] = Field(0.0015, description="Mie beta coefficient")
    g: Optional[float] = Field(-0.85, description="Mie phase asymmetry factor")
    sun_power: Optional[float] = Field(15.0, description="Sun power")
    samples: Optional[int] = Field(32, description="Number of samples")
    calc_in_fragment: Optional[bool] = Field(True, description="Calculate in fragment shader")
    normalize: Optional[bool] = Field(True, description="Normalize scattering result")
    hdr: Optional[bool] = Field(True, description="Enable HDR rendering")
    exposure: Optional[float] = Field(1, description="Exposure factor")
    atm_calc_in_fragment: Optional[bool] = Field(True, description="Atmosphere calculation in fragment shader")
    atm_normalize: Optional[bool] = Field(True, description="Atmosphere normalization")
    atm_hdr: Optional[bool] = Field(True, description="Atmosphere HDR")
    atm_exposure: Optional[float] = Field(0.8, description="Atmosphere exposure")
