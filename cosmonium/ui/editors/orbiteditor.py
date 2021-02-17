#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2021 Laurent Deru.
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

from ...parameters import ParametersList, UserParameter, AutoUserParameter

from math import pi
from cosmonium.parameters import ParametersGroup

class OrbitEditorBase():
    def __init__(self, orbit):
        self.orbit = orbit

    def get_group(self):
        group = None
        parameters =self.get_user_parameters()
        if not parameters.is_empty():
            group = ParametersGroup(_('Orbit'), parameters.parameters)
        return group

class EllipticalOrbitEditor(OrbitEditorBase):
    def get_user_parameters(self):
        parameters = ParametersList()
        parameters.add_parameters(
            UserParameter(_("Period"), self.orbit.set_period, self.orbit.get_period, UserParameter.TYPE_FLOAT),
            AutoUserParameter(_("Eccentricity"), "eccentricity", self.orbit, UserParameter.TYPE_FLOAT, value_range=[0, 10]),
            AutoUserParameter(_("Inclination"), "inclination", self.orbit, UserParameter.TYPE_FLOAT, value_range=[-180, 180], units=pi / 180),
            AutoUserParameter(_("Argument of periapsis"), 'arg_of_periapsis', self.orbit, UserParameter.TYPE_FLOAT, value_range=[-360, 360], units=pi / 180),
            AutoUserParameter(_("Ascending node"), 'ascending_node', self.orbit, UserParameter.TYPE_FLOAT, value_range=[-360, 360], units=pi / 180),
            AutoUserParameter(_("Mean anomaly"), 'mean_anomaly', self.orbit, UserParameter.TYPE_FLOAT, value_range=[-360, 360], units=pi / 180),
            AutoUserParameter(_("Epoch"), 'epoch', self.orbit, UserParameter.TYPE_FLOAT),
            )
        return parameters

    def update_user_parameters(self):
        self.orbit.update_rotation()
