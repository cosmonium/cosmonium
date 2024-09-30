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


from math import sqrt
from panda3d.core import LColor, LVector3

from ...datasource import DataSource
from ...shaders.lighting.scattering import ScatteringInterface as ShaderScatteringInterface
from ...shaders.scattering import AtmosphericScattering
from ..scattering import ScatteringBase


class AtmosphereFogScatteringShader(AtmosphericScattering, ShaderScatteringInterface):

    fragment_requires = {'world_vertex'}

    def __init__(self, atmosphere):
        AtmosphericScattering.__init__(self)
        self.atmosphere = atmosphere

    def get_id(self):
        return "fog"

    def fragment_uniforms(self, code):
        AtmosphericScattering.fragment_uniforms(self, code)
        if self.atmosphere:
            code.append("uniform vec3 sky_color;")
        else:
            code.append("uniform vec3 camera;")
            code.append("uniform vec3 sky_color;")
            code.append("uniform vec3 light_color;")
            code.append("uniform vec3 sun_color;")
            code.append("float fogFallOff = 0.00035;")

    def prepare_scattering_for(self, code, light_direction, light_color):
        pass

    def calc_transmittance(self, code):
        pass

    def incoming_light_for(self, code, light_direction, light_color):
        if self.atmosphere:
            code.append("    in_scatter = sky_color;")
        else:
            code.append("    float cam_distance = abs(distance(camera, world_vertex));")
            code.append("    float fogAmount = 1.0 - exp(-cam_distance * fogFallOff);")
            code.append("    in_scatter = sky_color * fogAmount;")
            code.append("    transmittance = vec3(1.0 - fogAmount);")
            code.append("    incoming_light_color = light_color;")
            code.append("    ambient_diffuse = sky_color * 0.3;")


class FogScatteringDataSource(DataSource):
    def __init__(self, parameters):
        DataSource.__init__(self, 'scattering')
        self.parameters = parameters

    def update(self, shape, instance, camera_pos, camera_rot):
        instance.set_shader_input("sky_color", self.parameters.sky_color)
        instance.set_shader_input("light_color", self.parameters.light_color)
        instance.set_shader_input("camera", 0, 0, 0)


class FogScattering(ScatteringBase):
    def __init__(self):
        super().__init__()
        self.light_color = (1.0, 1.0, 1.0, 1.0)
        self.sky_color_base = LColor(pow(0.5, 1 / 2.2), pow(0.6, 1 / 2.2), pow(0.7, 1 / 2.2), 1.0)
        self.sun_color_base = LColor(pow(1.0, 1 / 2.2), pow(0.9, 1 / 2.2), pow(0.7, 1 / 2.2), 1.0)
        self.sky_color = self.sky_color_base
        self.sun_color = self.sun_color_base

    def do_update_scattering(self, shape_object, atmosphere, extinction):
        pass

    def create_scattering_shader(self, atmosphere, displacement, extinction):
        return AtmosphereFogScatteringShader(atmosphere)

    def create_data_source(self, atmosphere):
        return FogScatteringDataSource(self)

    def set_light(self, light):
        self.light = light

    def update(self, time, dt):
        cosA = self.light.light_direction.dot(-LVector3.up())
        if cosA >= 0:
            coef = sqrt(cosA)
            self.light_color = (1, coef, coef, 1)
            self.sky_color = self.sky_color_base * cosA
            self.sun_color = self.sun_color_base * cosA
        else:
            self.light_color = (0, 0, 0, 1)
            self.sky_color = (0, 0, 0, 1)
            self.sun_color = (0, 0, 0, 1)
