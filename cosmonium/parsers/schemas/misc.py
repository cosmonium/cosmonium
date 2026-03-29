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
Miscellaneous configuration schemas.

Defines Pydantic models for various top-level objects that don't fit
in other categories (ships, controllers, plugins, attributions, etc.)
"""

from __future__ import annotations

from typing import Any, List, Literal, Optional, Union

from pydantic import Field

from .base import ConfigBase
from .types import AngleDegField, DistanceMField, Point3Field


class ScriptControllerConfig(ConfigBase):
    """Configuration for a script-based movement controller."""

    type: Literal['script'] = Field(default='script', description="Controller type")
    file: str = Field(..., description="Path to the controller script module")


class SurfaceControllerConfig(ConfigBase):
    """Configuration for a spherical surface movement controller."""

    type: Literal['surface'] = Field(default='surface', description="Controller type")
    long: AngleDegField = Field(0.0, description="Initial longitude (float in degrees, or [value, unit])")
    lat: AngleDegField = Field(0.0, description="Initial latitude (float in degrees, or [value, unit])")
    altitude: DistanceMField = Field(0.0, description="Initial altitude above surface (float in m, or [value, unit])")


class FlatSurfaceControllerConfig(ConfigBase):
    """Configuration for a flat terrain surface movement controller."""

    type: Literal['flat-surface'] = Field(default='flat-surface', description="Controller type")
    position: Optional[Point3Field] = Field([0, 0, 0], description="Initial position [x, y, z]")
    altitude: float = Field(0.0, description="Initial altitude above terrain")


class ShipConfig(ConfigBase):
    """Configuration for ships and cockpits."""

    type: Literal['ship', 'cockpit'] = Field(..., description="Object type")
    name: str = Field(..., description="Ship/cockpit name")

    # Ship properties
    radius: Optional[DistanceMField] = Field(10, description="Ship radius (float in m, or [value, unit])")
    camera_distance: Optional[float] = Field(None, description="Camera distance")
    camera_position: Optional[List[float]] = Field(None, description="Camera position")
    camera_position_units: Optional[str] = Field('m', description="Units for camera position")
    camera_rotation: Optional[Union[List[float], Any]] = Field(None, description="Camera rotation")

    # Appearance
    shape: Optional[Union[str, dict, Any]] = Field(None, description="Shape configuration")
    appearance: Optional[Union[str, dict, Any]] = Field(None, description="Appearance configuration")
    lighting_model: Optional[Union[str, dict, Any]] = Field(None, description="Lighting model")


class ControllerConfig(ConfigBase):
    """Configuration for standalone controllers."""

    type: Literal['controller'] = Field(default='controller', description="Object type")
    name: Optional[str] = Field(None, description="Controller name")
    body: str = Field(..., description="Body to attach controller to")

    # Controller type and parameters (any additional fields allowed for different controller types)
    script: Optional[Union[str, dict, Any]] = Field(None, description="Script controller configuration")
    surface: Optional[Union[str, dict, Any]] = Field(None, description="Surface controller configuration")
    flat_surface: Optional[Union[str, dict, Any]] = Field(None, description="Flat surface controller configuration")


class PluginConfig(ConfigBase):
    """Configuration for plugins."""

    type: Literal['plugin'] = Field(default='plugin', description="Object type")
    name: Optional[str] = Field(None, description="Plugin name")
    file: str = Field(..., description="Plugin file path")


class AttributionConfig(ConfigBase):
    """Configuration for a single data attribution."""

    type: Literal['attribution'] = Field(default='attribution', description="Object type")
    id: Optional[str] = Field(None, description="Attribution ID")
    name: str = Field(..., description="Attribution name")
    copyright: Optional[str] = Field(None, description="Copyright information")
    license: Optional[str] = Field(None, description="License information")
    url: Optional[str] = Field(None, description="Attribution URL")


class AttributionsConfig(ConfigBase):
    """Configuration for multiple attributions (dict of attributions)."""

    type: Literal['attributions'] = Field(default='attributions', description="Object type")
    # This will store a dict of attribution_id -> attribution data
    # The actual structure is handled by the parser
