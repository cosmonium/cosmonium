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


from .base import LightingModel


class FlatLightingModel(LightingModel):
    def get_id(self):
        return "flat"

    def fragment_shader(self, code):
        if self.appearance.has_surface:
            code.append("total_diffuse_color = surface_color;")
        if self.appearance.has_emission:
            code.append("total_emission_color = emission_color;")
        if self.appearance.has_transparency:
            #TODO: This should not be here!
            code.append("float alpha =  %s;" % self.shader.data_source.get_source_for('alpha'))
            code.append("total_diffuse_color.a *= alpha;")
