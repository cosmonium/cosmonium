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


from ..component import ShaderComponent


class ScatteringInterface:

    def prepare_scattering_for(self, code, light_direction, light_color):
        raise NotImplementedError()

    def calc_transmittance(self, code):
        raise NotImplementedError()

    def incoming_light_for(self, code, light_direction, light_color):
        raise NotImplementedError()


class NoScattering(ShaderComponent, ScatteringInterface):

    def prepare_scattering_for(self, code, light_direction, light_color):
        pass

    def calc_transmittance(self, code):
        code.append("    transmittance = vec3(1);")

    def incoming_light_for(self, code, light_direction, light_color):
        code.append(f"    incoming_light_color = {light_color}.rgb;")
        code.append("    in_scatter = vec3(0);")
