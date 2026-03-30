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
Coordinate frame configuration schemas.

Defines Pydantic models for reference frames.
"""

from typing import Literal, Optional

from pydantic import ConfigDict, Field

from .base import ConfigBase


class J2000EclipticFrameConfig(ConfigBase):
    """Configuration for J2000 Ecliptic frame."""

    type: Literal['j2000ecliptic'] = Field(default='j2000ecliptic', description="Frame type")
    center: Optional[str] = Field(None, description="Center body reference")


class J2000EquatorialFrameConfig(ConfigBase):
    """Configuration for J2000 Equatorial frame."""

    type: Literal['j2000equatorial'] = Field(default='j2000equatorial', description="Frame type")
    center: Optional[str] = Field(None, description="Center body reference")


class J2000BarycentricEclipticFrameConfig(ConfigBase):
    """Configuration for J2000 Barycentric Ecliptic frame."""

    type: Literal['j2000barycentricecliptic'] = Field(default='j2000barycentricecliptic', description="Frame type")


class J2000BarycentricEquatorialFrameConfig(ConfigBase):
    """Configuration for J2000 Barycentric Equatorial frame."""

    type: Literal['j2000barycentricequatorial'] = Field(default='j2000barycentricequatorial', description="Frame type")


class EquatorialFrameConfig(ConfigBase):
    """Configuration for equatorial frame."""

    type: Literal['equatorial'] = Field(default='equatorial', description="Frame type")
    center: Optional[str] = Field(None, description="Center body reference")
    ra: Optional[float] = Field(0.0, description="Right ascension in degrees")
    de: Optional[float] = Field(0.0, description="Declination in degrees")
    longitude: Optional[float] = Field(0.0, description="Longitude at node in degrees")


class MeanEquatorialFrameConfig(ConfigBase):
    """Configuration for mean equatorial frame."""

    type: Literal['mean-equatorial'] = Field(default='mean-equatorial', description="Frame type")
    center: Optional[str] = Field(None, description="Center body reference")


class FixedFrameConfig(ConfigBase):
    """Configuration for fixed/synchrone frame."""

    type: Literal['fixed'] = Field(default='fixed', description="Frame type")
    center: Optional[str] = Field(None, description="Center body reference")


class NamedFrameConfig(ConfigBase):
    """Named frame for database registration.

    Frame specific parameters are not specified, all extra parameters are forwarded
    to the appropriate frame sub-parser.
    """

    model_config = ConfigDict(extra='allow')  # Allow extra fields for frame-specific parameters
    name: str = Field(..., description="Name to register in the frames database")
