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
Base classes for configuration schemas.

This module provides the foundation for all configuration schemas,
including base classes, type helpers, and common validators.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


def to_kebab(name):
    return name.replace('_', '-')


class ConfigBase(BaseModel):
    """
    Base class for all configuration schemas.

    Features:
    - Forbids extra fields by default
    - Supports field aliases for kebab-case YAML keys
    - Allows population by both alias and field name
    - Provides .to_dict() method for conversion back to plain dicts
    """

    model_config = ConfigDict(
        extra='ignore',  # Reject unknown fields
        populate_by_name=True,  # Accept both snake_case and kebab-case
        str_strip_whitespace=True,  # Strip whitespace from strings
        validate_default=True,  # Validate default values
        alias_generator=to_kebab,  # Convert field names to kebab-case for YAML
    )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the configuration back to a plain dictionary.

        This is useful for backward compatibility with code expecting dicts.
        Uses the by_alias=True option to output kebab-case keys.

        Returns:
            Dictionary representation of the configuration
        """
        return self.model_dump(by_alias=True, exclude_none=True)


class IncludeConfig(ConfigBase):
    type: Literal['include'] = Field(default='include', description="Configuration include type")
    include: str = Field(..., description="Path to the included configuration file")
