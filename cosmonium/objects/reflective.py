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


from .stellarbody import StellarBody
from ..anchors import StellarAnchor


class ReflectiveBody(StellarBody):
    anchor_class = StellarAnchor.Reflective
    allow_scattering = True
    def __init__(self, *args, **kwargs):
        self.albedo = kwargs.pop('albedo', 0.5)
        StellarBody.__init__(self, *args, **kwargs)
        #TODO: This should be done in create_anchor
        self.anchor._albedo = self.albedo

    def is_emissive(self):
        return False

    def get_phase(self):
        #TODO: This should not be managed here
        if self.lights is None or len(self.lights.lights) == 0:
            print("No light source for phase")
            return 0.0
        light_source = self.lights.lights[0]
        if self.anchor.vector_to_obs is None or light_source.light_direction is None: return 0.0
        angle = self.anchor.vector_to_obs.dot(-light_source.light_direction)
        phase = (1.0 + angle) / 2.0
        return phase

    def start_shadows_update(self):
        for component in self.get_components():
            component.start_shadows_update()

    def self_shadows_update(self, light_source):
        self.surface.add_self_shadow(light_source)

    def add_shadow_target(self, light_source, target):
        for component in target.get_components():
            self.surface.add_shadow_target(light_source, component)

    def end_shadows_update(self):
        for component in self.get_components():
            component.end_shadows_update()

    def unconfigure_shape(self):
        StellarBody.unconfigure_shape(self)
        self.surface.remove_all_shadows()

    def create_components(self):
        StellarBody.create_components(self)
        #if self.light_source is None:
            #self.create_light()
        self.components.update_shader()

    def update_components(self, camera_pos):
        #if self.light_source is not None:
        #    self.update_light(camera_pos)
        pass

    def remove_components(self):
        #if self.light_source is not None:
            #self.remove_light()
        self.components.update_shader()
        StellarBody.remove_components(self)
