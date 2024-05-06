#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2024 Laurent Deru.
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

from ...parameters import ParametersGroup
from ...astro.orbits import FixedPosition

from .editors import ObjectEditors


class StellarObjectEditor:
    def __init__(self, stellar_object):
        self.stellar_object = stellar_object
        orbit = self.stellar_object.anchor.orbit
        if isinstance(orbit, FixedPosition) and self.stellar_object.system is not None:
            if self.stellar_object.system.orbit_object is not None:
                self.orbit_object = self.stellar_object.system.orbit_object
        else:
            self.orbit_object = self.stellar_object.orbit_object

    def get_user_parameters(self):
        group = ParametersGroup(self.stellar_object.get_name())
        orbit = self.stellar_object.anchor.orbit
        if isinstance(orbit, FixedPosition) and self.stellar_object.system is not None:
            orbit = self.stellar_object.system.anchor.orbit
        general_group = ParametersGroup(_('General'))
        self.orbit_editor = ObjectEditors.get_editor_for(orbit)
        general_group.add_parameter(self.orbit_editor.get_group())
        self.rotation_editor = ObjectEditors.get_editor_for(self.stellar_object.anchor.rotation)
        general_group.add_parameter(self.rotation_editor.get_group())
        group.add_parameter(general_group)
        # TODO: CompositeObject should have an iterator interface
        for component in self.stellar_object.components.components:
            component_group = component.get_user_parameters()
            if component_group is not None:
                group.add_parameter(component_group)
        return group

    def update_user_parameters(self):
        # TODO: CompositeObject should have an iterator interface
        for component in self.stellar_object.components.components:
            component.update_user_parameters()
        self.orbit_editor.update_user_parameters()
        if self.orbit_object is not None:
            self.orbit_object.update_user_parameters()
        self.rotation_editor.update_user_parameters()
