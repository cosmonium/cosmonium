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

from ..component import ShaderComponent


class ShaderLocalShadowsInterface:

    def prepare_shadow_for(self, code, light):
        pass

    def shadow_for(self, code, light):
        pass


class ShaderLocalShadows(ShaderComponent, ShaderLocalShadowsInterface):

    fragment_requires = {'eye_vertex'}

    def get_id(self):
        return 'ls'

    def vertex_outputs(self, code):
        code.append("out vec4 local_shadow_proj[8];")

    def prepare_shadow_for(self, code, light):
        code.append(f"    local_shadow_proj[{light}] = p3d_LightSource[{light}].shadowViewMatrix * eye_vertex4;")

    def fragment_inputs(self, code):
        code.append("in vec4 local_shadow_proj[8];")

    def shadow_for(self, code, light):
        code.append(f"shadow *= textureProj(p3d_LightSource[{light}].shadowMap, local_shadow_proj[{light}]);")
