#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
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

from __future__ import annotations

from ..base import StructuredShader, ShaderProgram
from ..component import ShaderComponent

from .passthrough import DefaultPassThroughVertexShader


class PostProcessShader(StructuredShader):

    def __init__(self, vertex_shader=None, fragment_shader=None):
        StructuredShader.__init__(self)
        if vertex_shader is None:
            vertex_shader = DefaultPassThroughVertexShader(self)
        self.vertex_shader = vertex_shader
        self.fragment_shader = fragment_shader

    def get_shader_id(self) -> str:
        name = "postprocess"
        vertex_name = self.vertex_shader.get_shader_id()
        if vertex_name != '':
            name += '-' + vertex_name
        name += '-' + self.fragment_shader.get_shader_id()
        return name


class SimplePostProcessFragmentShader(ShaderProgram):

    def __init__(self, process: ShaderComponent, output_type: str = 'vec3'):
        ShaderProgram.__init__(self, 'fragment')
        self.process = process
        self.config = None
        self.output_type = output_type

    def get_shader_id(self) -> str:
        return self.process.get_id()

    def create_outputs(self, code: list[str]) -> None:
        code.append(f"out {self.output_type} result;")

    def create_uniforms(self, code: list[str]) -> None:
        code.append("uniform sampler2D scene;")
        self.process.fragment_uniforms(code)

    def create_extra(self, code: list[str]) -> None:
        self.process.fragment_extra(code)

    def create_body(self, code: list[str]) -> None:
        code.append("  vec2 texcoord = gl_FragCoord.xy / textureSize(scene, 0);")
        code.append("  vec3 pixel_color = textureLod(scene, texcoord, 0).xyz;")
        self.process.fragment_shader(code)
