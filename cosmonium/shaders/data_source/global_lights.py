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


from .base import ShaderDataSource


class GlobalLightsShaderDataSource(ShaderDataSource):
    def __init__(self, lights):
        ShaderDataSource.__init__(self)
        self.lights = lights

    def get_id(self):
        return 'gl'

    def vertex_uniforms(self, code):
        code.append("uniform vec3 global_light_direction;")
        code.append("uniform vec3 global_light_eye_direction;")
        code.append("uniform vec4 global_light_color;")

    def fragment_uniforms(self, code):
        code.append("uniform vec3 global_light_direction;")
        code.append("uniform vec3 global_light_eye_direction;")
        code.append("uniform vec4 global_light_color;")

    def has_source_for(self, source):
        if source == 'global_lights':
            return True
        else:
            return False

    def get_source_for(self, source, param, error=True):
        if source == 'global_lights':
            return "global_light_"
        if error:
            print("Unknown source '%s' requested" % source)
        return ''
