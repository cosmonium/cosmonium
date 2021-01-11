#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2019 Laurent Deru.
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

from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import LQuaterniond, LVector3d

from ..parameters import ParametersGroup, UserParameter, AutoUserParameter

from .frame import J2000EquatorialReferenceFrame
from .astro import calc_orientation_from_incl_an
from . import units

from math import asin, atan2, pi

class ReferenceAxisBase(object):
    def get_user_parameters(self):
        return None

    def update_user_parameters(self):
        pass

    def get_rotation_at(self, time):
        return None

class ReferenceAxis(ReferenceAxisBase):
    def __init__(self, rotation):
        self.rotation = rotation

    def set_rotation(self, rotation):
        self.rotation = rotation

    def get_rotation_at(self, time):
        return self.rotation

class PlaneReferenceAxis(ReferenceAxisBase):
    def __init__(self, inclination, ascending_node, flipped):
        self.inclination = inclination
        self.ascending_node = ascending_node
        self.flipped = flipped
        self.rotation = None
        self.update_rotation()

    def get_rotation_at(self, time):
        return self.rotation

    def update_rotation(self):
        self.rotation = calc_orientation_from_incl_an(self.inclination, self.ascending_node, self.flipped)

    def get_user_parameters(self):
        parameters = [AutoUserParameter(_("Inclination"), 'inclination', self, AutoUserParameter.TYPE_FLOAT, value_range=[-180, 180], units=pi / 180),
                      AutoUserParameter(_("Ascending node"), 'ascending_node', self, AutoUserParameter.TYPE_FLOAT, value_range=[-360, 360], units=pi / 180),
                     ]
        return parameters

    def update_user_parameters(self):
        self.update_rotation()

class EquatorialReferenceAxis(ReferenceAxisBase):
    def __init__(self, right_ascension, declination, flipped):
        self.right_ascension = right_ascension
        self.declination = declination
        self.flipped = flipped
        self.rotation = None
        self.update_rotation()

    def get_rotation_at(self, time):
        return self.rotation

    def update_rotation(self):
        inclination = pi / 2 - self.declination
        ascending_node = self.right_ascension + pi / 2
        # The rotation into the equatorial plane is done in the reference frame
        self.rotation = calc_orientation_from_incl_an(inclination, ascending_node, self.flipped)

    def get_user_parameters(self):
        parameters = [AutoUserParameter(_("Declination"), 'declination', self, AutoUserParameter.TYPE_FLOAT, value_range=[-180, 180], units=pi / 180),
                      AutoUserParameter(_("Right ascension"), 'right_ascension', self, AutoUserParameter.TYPE_FLOAT, value_range=[0, 360], units=pi / 180),
                     ]
        return parameters

    def update_user_parameters(self):
        self.update_rotation()

class Rotation(object):
    dynamic = False
    def __init__(self, frame):
        self.frame = frame

    def is_flipped(self):
        return False

    def get_user_parameters(self):
        group = ParametersGroup(_('Rotation'))
        return group

    def update_user_parameters(self):
        pass

    def set_frame(self, frame):
        self.frame = frame

    def get_frame_equatorial_orientation_at(self, time):
        return None

    def get_equatorial_orientation_at(self, time):
        return self.frame.get_absolute_orientation(self.get_frame_equatorial_orientation_at(time))

    def get_frame_rotation_at(self, time):
        return None

    def get_absolute_rotation_at(self, time):
        return self.frame.get_absolute_orientation(self.get_frame_rotation_at(time))

class FixedRotation(Rotation):
    def __init__(self, reference_axis, frame):
        Rotation.__init__(self, frame)
        if isinstance(reference_axis, LQuaterniond):
            reference_axis = ReferenceAxis(reference_axis)
        self.reference_axis = reference_axis

    def get_user_parameters(self):
        group = Rotation.get_user_parameters(self)
        group.add_parameters(self.reference_axis.get_user_parameters())
        return group

    def update_user_parameters(self):
        self.reference_axis.update_user_parameters()

    def get_frame_equatorial_orientation_at(self, time):
        return self.reference_axis.get_rotation_at(time)

    def get_frame_rotation_at(self, time):
        return self.reference_axis.get_rotation_at(time)

    def calc_axis_ra_de(self, time):
        rotation = self.get_equatorial_orientation_at(time)
        axis = rotation.xform(LVector3d.up())
        axis = self.frame.get_orientation().xform(axis)
        projected = J2000EquatorialReferenceFrame.orientation.conjugate().xform(axis)
        declination = asin(projected[2])
        right_asc = atan2(projected[1], projected[0])
        if right_asc < 0:
            right_asc += 2 * pi
        return (right_asc, declination)

class UnknownRotation(FixedRotation):
    def __init__(self):
        FixedRotation.__init__(self, ReferenceAxis(LQuaterniond()), J2000EquatorialReferenceFrame())

class UniformRotation(FixedRotation):
    dynamic = True
    def __init__(self,
                 period,
                 reference_axis,
                 meridian_angle,
                 epoch,
                 frame):
        FixedRotation.__init__(self, reference_axis, frame)
        self.set_period(period)
        self.epoch = epoch
        self.meridian_angle = meridian_angle

    def is_flipped(self):
        return self.period < 0

    def set_period(self, period):
        self.period = period
        if period != 0:
            self.mean_motion = 2 * pi / period
        else:
            self.mean_motion = 0

    def get_period(self):
        return self.period

    def get_user_parameters(self):
        group = FixedRotation.get_user_parameters(self)
        group.add_parameter(UserParameter(_("Period"), self.set_period, self.get_period, UserParameter.TYPE_FLOAT))
        group.add_parameter(AutoUserParameter(_("Meridian angle"), 'meridian_angle', self, UserParameter.TYPE_FLOAT, value_range=[-360, 360], units=pi / 180))
        group.add_parameter(AutoUserParameter(_("Epoch"), 'epoch', self, UserParameter.TYPE_FLOAT))
        return group

    def get_frame_rotation_at(self, time):
        angle = (time - self.epoch) * self.mean_motion + self.meridian_angle
        local = LQuaterniond()
        if self.mean_motion < 0:
            angle = -angle
        local.setFromAxisAngleRad(angle, LVector3d.unitZ())
        rotation = local * self.get_frame_equatorial_orientation_at(time)
        return rotation

class SynchronousRotation(FixedRotation):
    def __init__(self,
                 reference_axis,
                 meridian_angle,
                 epoch,
                 frame=None):
        FixedRotation.__init__(self, reference_axis, frame)
        self.epoch = epoch
        self.meridian_angle = meridian_angle

    def get_user_parameters(self):
        group = FixedRotation.get_user_parameters(self)
        group.add_parameter(AutoUserParameter(_("Meridian angle"), 'meridian_angle', self, UserParameter.TYPE_FLOAT, value_range=[-360, 360], units=pi / 180))
        group.add_parameter(AutoUserParameter(_("Epoch"), 'epoch', self, UserParameter.TYPE_FLOAT))
        return group

    def get_frame_rotation_at(self, time):
        angle = (time - self.epoch) * self.body.anchor.orbit.get_mean_motion() + self.meridian_angle
        local = LQuaterniond()
        local.setFromAxisAngleRad(angle, LVector3d.unitZ())
        rotation = local * self.get_frame_equatorial_orientation_at(time)
        return rotation

class FuncRotation(Rotation):
    def __init__(self, rotation):
        Rotation.__init__(self, frame=J2000EquatorialReferenceFrame())
        self.rotation = rotation

    def is_flipped(self):
        return self.rotation.is_flipped()

    def get_frame_equatorial_orientation_at(self, time):
        return self.rotation.get_frame_equatorial_orientation_at(time)

    def get_frame_rotation_at(self, time):
        return self.rotation.get_frame_rotation_at(time)

def create_fixed_rotation(
             inclination=0.0, inclination_units=units.Deg,
             ascending_node=0.0, ascending_node_units=units.Deg,
                 right_asc=None, right_asc_unit=units.Deg,
                 declination=None, declination_unit=units.Deg,
                 frame=None):
    if right_asc is not None:
        reference_axis = EquatorialReferenceAxis(right_asc * right_asc_unit, declination * declination_unit)
        frame = J2000EquatorialReferenceFrame()
    else:
        reference_axis = PlaneReferenceAxis(inclination * inclination_units, ascending_node * ascending_node_units)
    if frame is None:
        frame = J2000EquatorialReferenceFrame()
    return FixedRotation(reference_axis, frame)

def create_uniform_rotation(
             period=None,
             period_units=units.Hour,
             sync=False,
             inclination=0.0, inclination_units=units.Deg,
             ascending_node=0.0, ascending_node_units=units.Deg,
             right_asc=None, right_asc_unit=units.Deg,
             declination=None, declination_unit=units.Deg,
             meridian_angle=0.0, meridian_units=units.Deg,
             epoch=units.J2000,
             frame=None):
    flipped = period is not None and period < 0
    if right_asc is not None:
        reference_axis = EquatorialReferenceAxis(right_asc * right_asc_unit, declination * declination_unit, flipped)
        frame = J2000EquatorialReferenceFrame()
    else:
        reference_axis = PlaneReferenceAxis(inclination * inclination_units, ascending_node * ascending_node_units, flipped)
    if frame is None:
        frame = J2000EquatorialReferenceFrame()
    meridian_angle = meridian_angle * meridian_units
    if sync:
        return SynchronousRotation(reference_axis, meridian_angle, epoch, frame)
    else:
        if period is not None:
            period = period * period_units
        else:
            period = 0.0
        return UniformRotation(period, reference_axis, meridian_angle, epoch, frame)
