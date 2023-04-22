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


from ..component import CompositeShaderComponent
from .scattering import NoScattering


class PureEmissionLightingModel(CompositeShaderComponent):

    def __init__(self):
        CompositeShaderComponent.__init__(self)
        self.scattering = NoScattering()
        self.add_component(self.scattering)
        self._appearance = None

    @property
    def appearance(self):
        return self._appearance

    @appearance.setter
    def appearance(self, appearance):
        self._appearance = appearance
        for component in self.components:
            component.appearance = appearance

    def set_scattering(self, scattering):
        self.remove_component(self.scattering)
        self.scattering = scattering
        self.add_component(self.scattering)

    def vertex_shader(self, code):
        CompositeShaderComponent.vertex_shader(self, code)
        global_lights = self.shader.data_source.get_source_for('global_lights')
        code.append("for (int i = 0; i < 1; ++i) {")
        self.scattering.prepare_scattering_for(code, global_lights + "eye_direction", global_lights + "color")
        code.append("}")

    def fragment_shader(self, code):
        code.append("  vec3 transmittance;")
        self.scattering.calc_transmittance(code)
        if self.appearance.has_surface:
            code.append("total_diffuse_color = surface_color;")
        if self.appearance.has_emission:
            code.append("total_emission_color = emission_color;")
        if self.appearance.has_transparency:
            #TODO: This should not be here!
            code.append("float alpha =  %s;" % self.shader.data_source.get_source_for('alpha'))
            code.append("total_diffuse_color.a *= alpha;")
