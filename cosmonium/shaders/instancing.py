#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2022 Laurent Deru.
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


from .component import ShaderComponent
from .. import settings

class InstanceControl(ShaderComponent):
    def __init__(self, max_instances):
        ShaderComponent.__init__(self)
        self.max_instances = max_instances

    def update_vertex(self, code):
        pass

    def update_normal(self, code):
        pass

class NoInstanceControl(InstanceControl):
    def __init__(self):
        InstanceControl.__init__(self, 0)

class OffsetScaleInstanceControl(InstanceControl):
    use_vertex = True
    world_vertex = True
    def get_id(self):
        return "offset%d" % self.max_instances

    def vertex_uniforms(self, code):
        if settings.instancing_use_tex:
            code.append("uniform samplerBuffer instances_offset;")
        else:
            code.append("uniform vec4 instances_offset[%d];" % self.max_instances)

    def update_vertex(self, code):
        if settings.instancing_use_tex:
            code.append("vec4 offset_data = texelFetch(instances_offset, gl_InstanceID);")
        else:
            code.append("vec4 offset_data = instances_offset[gl_InstanceID];")
        code.append("world_vertex4 = p3d_ModelMatrix * vec4(model_vertex4.xyz * offset_data.w, model_vertex4.w);")
        code.append("world_vertex4 = world_vertex4 + vec4(offset_data.xyz, 0.0);")
