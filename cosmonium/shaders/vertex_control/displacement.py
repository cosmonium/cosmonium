#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2023 Laurent Deru.
#
#Cosmonium is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Cosmonium is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#


from .vertex_control import VertexControl


class DisplacementVertexControl(VertexControl):

    vertex_provides = {'model_vertex'} #'model_normal
    vertex_requires = {'tangent'}

    def __init__(self, heightmap, create_normals=False):
        VertexControl.__init__(self)
        self.heightmap = heightmap
        self.has_normal = create_normals
        if create_normals:
            self.use_tangent = True

    def get_id(self):
        return "dis-" + self.heightmap.name

    def vertex_outputs(self, code):
        code.append('out float vertex_height;')

    def fragment_inputs(self, code):
        code.append("in float vertex_height;")

    def update_vertex(self, code):
        code.append("vertex_height = %s;" % self.shader.data_source.get_source_for('height_%s' % self.heightmap.name, 'model_texcoord0.xy'))
        code.append("model_vertex4 = model_vertex4 + model_normal4 * vertex_height;")

    def update_normal(self, code):
        code.append("vec3 normal = model_normal4.xyz;")
        code.append('vec3 surface_normal = %s;' % self.shader.data_source.get_source_for('normal_%s' % self.heightmap.name, 'model_texcoord0.xy'))
        code.append("normal *= surface_normal.z;")
        code.append("normal += model_tangent4.xyz * surface_normal.x;")
        code.append("normal += model_tangent4.xyz * surface_normal.y;")
        code.append("normal = normalize(normal);")
        code.append("model_normal4 = vec4(normal, 0.0);")
