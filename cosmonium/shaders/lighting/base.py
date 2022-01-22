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


from ..component import ShaderComponent


class LightingModel(ShaderComponent):
    def fragment_uniforms(self, code):
        if self.appearance.has_emission and self.appearance.has_nightscale:
            code.append("uniform float nightscale;")

    def apply_emission(self, code, angle):
        back_test = self.appearance.has_backlit or (self.appearance.has_emission and self.appearance.has_nightscale)
        if back_test:
            code.append("if (%s < 0.0) {" % angle)
        if self.appearance.has_emission and self.appearance.has_nightscale:
            code.append("  float emission_coef = clamp(sqrt(-%s), 0.0, 1.0) * nightscale;" % angle)
            code.append("  total_emission_color.rgb += emission_color.rgb * emission_coef;")
        if self.appearance.has_backlit:
            code.append("  total_emission_color.rgb += surface_color.rgb * backlit * sqrt(-%s) * shadow;" % angle)
        if back_test:
            code.append("}")
        if self.appearance.has_emission and not self.appearance.has_nightscale:
            code.append("  total_emission_color.rgb += emission_color.rgb;")
