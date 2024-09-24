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

from .vertex_control import VertexControl


class NormalizedCubeVertexControl(VertexControl):

    vertex_requires = {'model_vertex'}
    vertex_provides = {'model_vertex', 'model_normal', 'tangent'}

    def get_id(self):
        return "normcube"

    def vertex_uniforms(self, code):
        code.append("uniform vec3 patch_offset;")

    def update_vertex(self, code):
        code.append("model_vertex4 = vec4(normalize(model_vertex4.xyz), model_vertex4.w);")
        code.append("vec4 source_vertex4 = model_vertex4;")
        code.append("model_vertex4.xyz -= patch_offset;")

    def update_normal(self, code):
        code.append("model_normal4 = vec4(source_vertex4.xyz, 0.0);")
        if self.shader.use_tangent:
            code.append("model_tangent4 = vec4(source_vertex4.z, source_vertex4.y, -source_vertex4.x, 0.0);")
            code.append("model_binormal4 = vec4(source_vertex4.x, source_vertex4.z, -source_vertex4.y, 0.0);")

    def update_shader_patch_static(self, shape, patch, appearance):
        patch.instance.set_shader_input('patch_offset', patch.source_normal * patch.offset)


class SquaredDistanceCubeVertexControl(VertexControl):

    vertex_requires = {'model_vertex'}
    vertex_provides = {'model_vertex', 'model_normal', 'tangent'}

    def get_id(self):
        return "sqrtcube"

    def vertex_uniforms(self, code):
        code.append("uniform vec3 patch_offset;")

    def update_vertex(self, code):
        code.append("float x2 = model_vertex4.x * model_vertex4.x;")
        code.append("float y2 = model_vertex4.y * model_vertex4.y;")
        code.append("float z2 = model_vertex4.z * model_vertex4.z;")
        code.append("model_vertex4.x *= sqrt(1.0 - y2 * 0.5 - z2 * 0.5 + y2 * z2 / 3.0);")
        code.append("model_vertex4.y *= sqrt(1.0 - z2 * 0.5 - x2 * 0.5 + z2 * x2 / 3.0);")
        code.append("model_vertex4.z *= sqrt(1.0 - x2 * 0.5 - y2 * 0.5 + x2 * y2 / 3.0);")
        code.append("vec4 source_vertex4 = model_vertex4;")
        code.append("model_vertex4.xyz -= patch_offset;")

    def update_normal(self, code):
        code.append("model_normal4 = vec4(source_vertex4.xyz, 0.0);")
        if self.shader.use_tangent:
            code.append("model_tangent4 = vec4(source_vertex4.z, source_vertex4.y, -source_vertex4.x, 0.0);")
            code.append("model_binormal4 = vec4(source_vertex4.x, source_vertex4.z, -source_vertex4.y, 0.0);")

    def update_shader_patch_static(self, shape, patch, appearance):
        patch.instance.set_shader_input('patch_offset', patch.source_normal * patch.offset)


class DoubleSquaredDistanceCubeVertexControl(VertexControl):

    vertex_requires = {'model_vertex'}
    vertex_provides = {'model_vertex', 'model_normal', 'tangent'}

    def get_id(self):
        return "sqrtcubedouble"

    def vertex_uniforms(self, code):
        code.append("uniform vec3 patch_offset;")

    def update_vertex(self, code):
        code.append("dvec4 double_model_vertex4 = dvec4(model_vertex4) + dvec4(0, 0, 1, 0);")
        code.append("double x2 = double_model_vertex4.x * double_model_vertex4.x;")
        code.append("double y2 = double_model_vertex4.y * double_model_vertex4.y;")
        code.append("double z2 = double_model_vertex4.z * double_model_vertex4.z;")

        code.append("double_model_vertex4.x *= sqrt(1.0 - y2 * 0.5 - z2 * 0.5 + y2 * z2 / 3.0);")
        code.append("double_model_vertex4.y *= sqrt(1.0 - z2 * 0.5 - x2 * 0.5 + z2 * x2 / 3.0);")
        code.append("double_model_vertex4.z *= sqrt(1.0 - x2 * 0.5 - y2 * 0.5 + x2 * y2 / 3.0);")
        code.append("double_model_vertex4.xyz -= dvec3(patch_offset);")
        code.append("model_vertex4 = vec4(double_model_vertex4);")

    def update_normal(self, code):
        code.append("model_normal4 = vec4(model_vertex4.xyz, 0.0);")

    def update_shader_patch_static(self, shape, patch, appearance):
        patch.instance.set_shader_input('patch_offset', patch.source_normal * patch.offset)
