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

from math import pi

from ...astro.astro import calc_orientation, calc_orientation_from_incl_an, orientation_to_equatorial
from ...astro import units
from ...parameters import ParametersList, ParametersGroup, UserParameter, AutoUserParameter


class RotationEditorBase:

    def __init__(self, rotation):
        self.rotation = rotation
        self.equatorial = True
        if self.equatorial:
            self.right_ascension, self.declination = orientation_to_equatorial(
                self.rotation.get_equatorial_orientation_at(0)
            )
        else:
            pass  # TODO: conversion is missing for inclination and ascending node

    def get_group(self):
        group = None
        parameters = self.get_user_parameters()
        if not parameters.is_empty():
            group = ParametersGroup(_('Rotation'), parameters.parameters)
        return group

    def get_user_parameters(self):
        parameters = ParametersList()
        if self.equatorial:
            parameters.add_parameters(
                AutoUserParameter(
                    _("Declination"),
                    'declination',
                    self,
                    AutoUserParameter.TYPE_FLOAT,
                    value_range=[-90, 90],
                    units=pi / 180,
                ),
                AutoUserParameter(
                    _("Right ascension"),
                    'right_ascension',
                    self,
                    AutoUserParameter.TYPE_FLOAT,
                    value_range=[0, 360],
                    units=pi / 180,
                ),
            )
        else:
            parameters.add_parameters(
                AutoUserParameter(
                    _("Inclination"),
                    'inclination',
                    self,
                    AutoUserParameter.TYPE_FLOAT,
                    value_range=[-90, 90],
                    units=pi / 180,
                ),
                AutoUserParameter(
                    _("Ascending node"),
                    'ascending_node',
                    self,
                    AutoUserParameter.TYPE_FLOAT,
                    value_range=[-180, 180],
                    units=pi / 180,
                ),
            )
        return parameters

    def update_user_parameters(self):
        if self.equatorial:
            equatorial_orientation = calc_orientation(
                self.right_ascension, self.declination, self.rotation.is_flipped()
            )
            equatorial_orientation = equatorial_orientation * units.J2000_Orientation
        else:
            equatorial_orientation = calc_orientation_from_incl_an(
                self.inclination, self.ascending_node, self.rotation.is_flipped()
            )
        equatorial_orientation = self.rotation.frame.get_frame_orientation(equatorial_orientation)
        self.rotation.equatorial_orientation = equatorial_orientation


class UniformRotationEditor(RotationEditorBase):

    def get_user_parameters(self):
        parameters = RotationEditorBase.get_user_parameters(self)
        parameters.add_parameter(
            UserParameter(_("Period"), self.rotation.set_period, self.rotation.get_period, UserParameter.TYPE_FLOAT)
        )
        parameters.add_parameter(
            AutoUserParameter(
                _("Meridian angle"),
                'meridian_angle',
                self.rotation,
                UserParameter.TYPE_FLOAT,
                value_range=[-360, 360],
                units=pi / 180,
            )
        )
        parameters.add_parameter(AutoUserParameter(_("Epoch"), 'epoch', self.rotation, UserParameter.TYPE_FLOAT))
        return parameters

    def update_user_parameters(self):
        RotationEditorBase.update_user_parameters(self)
