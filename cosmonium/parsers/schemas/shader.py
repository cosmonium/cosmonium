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


"""Shader configuration schemas."""

from __future__ import annotations

from typing import List, Literal

from pydantic import Field

from .base import ConfigBase


class CustomShaderComponentConfig(ConfigBase):
    """Configuration for a custom shader component."""

    type: Literal['custom'] = Field(default='custom', description="Shader component type")

    # Requirements and provisions
    vertex_requires: List[str] = Field(default_factory=list, description="Vertex shader requirements")
    vertex_provides: List[str] = Field(default_factory=list, description="Vertex shader provisions")
    fragment_requires: List[str] = Field(default_factory=list, description="Fragment shader requirements")
    fragment_provides: List[str] = Field(default_factory=list, description="Fragment shader provisions")

    # Vertex shader code blocks
    vertex_uniforms: str = Field('', description="Vertex uniform declarations")
    vertex_inputs: str = Field('', description="Vertex input declarations")
    vertex_outputs: str = Field('', description="Vertex output declarations")
    vertex_extra: str = Field('', description="Extra vertex declarations")
    update_vertex: str = Field('', description="Vertex update code")
    update_normal: str = Field('', description="Normal update code")
    vertex_shader: str = Field('', description="Main vertex shader code")

    # Fragment shader code blocks
    fragment_uniforms: str = Field('', description="Fragment uniform declarations")
    fragment_inputs: str = Field('', description="Fragment input declarations")
    fragment_extra: str = Field('', description="Extra fragment declarations")
    fragment_shader_decl: str = Field('', description="Fragment shader declarations")
    fragment_shader_distort_coord: str = Field('', description="Fragment shader coordinate distortion code")
    fragment_shader: str = Field('', description="Main fragment shader code")
