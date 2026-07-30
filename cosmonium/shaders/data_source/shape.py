#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2025 Laurent Deru.
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


from .base import ShaderDataSource


class SpherifiedCubeGeometryShaderDataSource(ShaderDataSource):

    vertex_provides = {'jacobian'}

    def get_id(self):
        return 'scj'

    def vertex_inputs(self, code):
        code.append('in vec3 jacobian_params;')

    def vertex_outputs(self, code):
        code.append('out mat3 jacobian;')

    def vertex_shader(self, code):
        code.append('''
    {
        float x = jacobian_params.x;
        float y = jacobian_params.y;
        float iw2 = jacobian_params.z;
        jacobian = mat3(
            1 - x * x * iw2, -x * y * iw2, -x * iw2,
            -x * y * iw2, 1 - y * y * iw2, -y * iw2,
            x, y, 1
        );
    }
''')

    def fragment_inputs(self, code):
        code.append('in mat3 jacobian;')


class ImprovedSpherifiedCubeGeometryShaderDataSource(ShaderDataSource):

    vertex_provides = {'jacobian'}

    def get_id(self):
        return 'iscj'

    def vertex_inputs(self, code):
        code.append('in vec4 jacobian_params;')

    def vertex_outputs(self, code):
        code.append('out mat3 jacobian;')

    def vertex_shader(self, code):
        code.append('''
    {
        float s2 = jacobian_params.x * jacobian_params.x;
        float t2 = jacobian_params.y * jacobian_params.y;
        float a = jacobian_params.z;
        float b = jacobian_params.w;
        float w = sqrt(s2 * t2 / 3 - 0.5 * s2 - 0.5 * t2 + 1);
        jacobian = mat3(
            b, -jacobian_params.x * jacobian_params.y / (6 * a), jacobian_params.x * (t2 / 3 - 0.5) / w,
            -jacobian_params.x * jacobian_params.y / (6 * b), a, jacobian_params.y * (s2 / 3 - 0.5) / w,
            jacobian_params.x * b, jacobian_params.y * a, w
        );
    }
''')

    def fragment_inputs(self, code):
        code.append('in mat3 jacobian;')
