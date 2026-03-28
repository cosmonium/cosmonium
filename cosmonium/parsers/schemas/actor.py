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
Actor configuration schemas.

Defines Pydantic models for actor objects and actor shapes (animated mesh entities).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import Field

from .base import ConfigBase


class ActorShapeConfig(ConfigBase):
    """Configuration for an actor (animated) shape."""

    model: str = Field(..., description="Path to the model file")
    animations: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Animation name to file path mapping"
    )
    panda: bool = Field(True, description="Use Panda3D native model format")
    auto_scale: bool = Field(False, description="Automatically scale mesh to target radius")
    auto_center: bool = Field(False, description="Automatically center mesh at origin")
    offset: Optional[List[float]] = Field(None, description="Mesh positional offset [x, y, z]")
    rotation: Optional[List[float]] = Field(
        None, description="Mesh rotation as HPR (3 values) or quaternion (4 values)"
    )
    scale: Optional[Union[float, List[float]]] = Field(None, description="Scale factor (uniform) or [x, y, z]")
    flatten: bool = Field(True, description="Flatten the scene graph hierarchy for performance")
    attribution: Optional[str] = Field(None, description="Attribution/credit for the model")


class ActorObjectConfig(ConfigBase):
    """Configuration for an actor object entity."""

    name: Optional[str] = Field(None, description="Actor name")
    shape: Optional[Any] = Field(None, description="Shape configuration")
    appearance: Optional[Any] = Field(None, description="Appearance configuration")
    lighting_model: Optional[Any] = Field(None, description="Lighting model configuration")
