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

from .frame import J2000EquatorialReferenceFrame
from . import units

from math import asin, atan2, pi
from cosmonium.astro.astro import calc_orientation_from_incl_an

class Rotation(object):
    dynamic = False
    def __init__(self, frame):
        self.frame = frame

    def set_frame(self, frame):
        self.frame = frame

    def get_frame_equatorial_orientation_at(self, time):
        return None

    def get_equatorial_orientation_at(self, time):
        return self.frame.get_abs_orientation(self.get_frame_equatorial_orientation_at(time))

    def get_frame_rotation_at(self, time):
        return None

    def get_rotation_at(self, time):
        return self.frame.get_abs_orientation(self.get_frame_rotation_at(time))

class FixedRotation(Rotation):
    def __init__(self, rotation, frame):
        Rotation.__init__(self, frame)
        self.axis_rotation = rotation
        self.rotation = LQuaterniond()

    def get_frame_equatorial_orientation_at(self, time):
        return self.axis_rotation

    def get_frame_rotation_at(self, time):
        return self.axis_rotation

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
        FixedRotation.__init__(self, LQuaterniond(), J2000EquatorialReferenceFrame())

class UniformRotation(FixedRotation):
    dynamic = True
    def __init__(self,
                 period,
                 rotation,
                 meridian_angle,
                 epoch,
                 frame):
        FixedRotation.__init__(self, rotation, frame)
        self.period = period
        if period != 0:
            self.mean_motion = 2 * pi / period
        else:
            self.mean_motion = 0
        self.epoch = epoch
        self.meridian_angle = meridian_angle

    def get_frame_rotation_at(self, time):
        angle = (time - self.epoch) * self.mean_motion + self.meridian_angle
        local = LQuaterniond()
        local.setFromAxisAngleRad(angle, LVector3d.unitZ())
        rotation = local * self.get_frame_equatorial_orientation_at(time)
        return rotation

class SynchronousRotation(FixedRotation):
    def __init__(self,
                 rotation,
                 meridian_angle,
                 epoch,
                 frame=None):
        FixedRotation.__init__(self, rotation, frame)
        self.epoch = epoch
        self.meridian_angle = meridian_angle * pi / 180

    def get_frame_rotation_at(self, time):
        angle = (time - self.epoch) * self.body.orbit.get_mean_motion() + self.meridian_angle
        local = LQuaterniond()
        local.setFromAxisAngleRad(angle, LVector3d.unitZ())
        rotation = local * self.get_frame_equatorial_orientation_at(time)
        return rotation

def create_fixed_rotation(
                 inclination=0.0,
                 ascending_node=0.0,
                 right_asc=None, right_asc_unit=units.Deg,
                 declination=None, declination_unit=units.Deg,
                 frame=None):
    if right_asc is None:
        inclination = inclination * pi / 180
        ascending_node = ascending_node * pi / 180
        rotation = calc_orientation_from_incl_an(inclination, ascending_node, False)
    else:
        right_asc = right_asc * right_asc_unit
        declination = declination * declination_unit
        inclination = pi / 2 - declination
        ascending_node = right_asc + pi / 2
        rotation = calc_orientation_from_incl_an(inclination, ascending_node, True)
    return FixedRotation(rotation, frame)

def create_uniform_rotation(
             period=None,
             period_units=units.Hour,
             sync=False,
             inclination=0.0,
             ascending_node=0.0,
             right_asc=None, right_asc_unit=units.Deg,
             declination=None, declination_unit=units.Deg,
             meridian_angle=0.0,
             epoch=units.J2000,
             frame=None):

    if right_asc is None:
        inclination = inclination * pi / 180
        ascending_node = ascending_node * pi / 180
    else:
        right_asc = right_asc * right_asc_unit
        declination = declination * declination_unit
        inclination = pi / 2 - declination
        ascending_node = right_asc + pi / 2
    rotation = calc_orientation_from_incl_an(inclination, ascending_node, False)
    meridian_angle = meridian_angle * pi / 180
    if frame is None:
        frame = J2000EquatorialReferenceFrame()
    if sync:
        return SynchronousRotation(rotation, meridian_angle, epoch, frame)
    else:
        if period is not None:
            period = period * period_units
        else:
            period = 0.0
        return UniformRotation(period, rotation, meridian_angle, epoch, frame)
