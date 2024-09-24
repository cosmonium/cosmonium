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


class LargeObjectVertexControl(VertexControl):

    vertex_provides = {'world_vertex'}

    def get_id(self):
        return "lo"

    def vertex_uniforms(self, code):
        code.append("uniform float midPlane;")

    def update_vertex(self, code):
        code.append("world_vertex4 = p3d_ModelMatrix * model_vertex4;")
        code.append("float distance_to_obs = length(vec3(world_vertex4));")
        code.append("if (distance_to_obs > midPlane) {")
        code.append("  vec3 vector_to_point = world_vertex4.xyz / distance_to_obs;")
        code.append("  vec3 not_scaled = vector_to_point * midPlane;")
        code.append("  float scaled_distance = midPlane * (1.0 - midPlane/distance_to_obs);")
        code.append("  vec3 scaled = vector_to_point * scaled_distance;")
        code.append("  world_vertex4.xyz = not_scaled + scaled;")
        code.append("}")
