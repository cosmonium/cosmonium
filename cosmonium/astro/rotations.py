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

import math

class Rotation(object):
    dynamic = False
    def __init__(self, frame=None):
        if frame is None:
            frame = J2000EquatorialReferenceFrame()
        self.frame = frame

    def set_frame(self, frame):
        self.frame = frame

    def get_equatorial_rotation_at(self, time):
        return None

    def get_rotation_at(self, time):
        return None

class FixedRotation(Rotation):
    def __init__(self,
                 rotation=None,
                 inclination=0.0,
                 ascending_node=0.0,
                 right_asc=None, right_asc_unit=units.Deg,
                 declination=None, declination_unit=units.Deg,
                 frame=None):
        Rotation.__init__(self, frame)
        if rotation is None:
            if right_asc is None:
                self.inclination = inclination * math.pi / 180
                self.ascending_node = ascending_node * math.pi / 180
                inclination_quat = LQuaterniond()
                inclination_quat.setFromAxisAngleRad(self.inclination, LVector3d.unitX())
                ascending_node_quat = LQuaterniond()
                ascending_node_quat.setFromAxisAngleRad(self.ascending_node, LVector3d.unitZ())
                rotation = inclination_quat * ascending_node_quat
            else:
                right_asc = right_asc * right_asc_unit
                declination = declination * declination_unit
                self.inclination = math.pi / 2 - declination
                self.ascending_node = right_asc + math.pi / 2
                inclination_quat = LQuaterniond()
                inclination_quat.setFromAxisAngleRad(self.inclination, LVector3d.unitX())
                ascending_node_quat = LQuaterniond()
                ascending_node_quat.setFromAxisAngleRad(self.ascending_node, LVector3d.unitZ())
                rotation = inclination_quat * ascending_node_quat
        self.axis_rotation = rotation
        self.rotation = LQuaterniond()

    def get_equatorial_rotation_at(self, time):
        return self.axis_rotation

    def get_rotation_at(self, time):
        return self.axis_rotation
    
class UniformRotation(FixedRotation):
    dynamic = True
    def __init__(self,
                 radial_speed=None,
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
        FixedRotation.__init__(self, None, inclination, ascending_node,
                               right_asc=right_asc, right_asc_unit=right_asc_unit, declination=declination, declination_unit=declination_unit,
                               frame=frame)
        if radial_speed is None:
            if period is None:
                self.mean_motion = 0.0
                self.period = 0.0
                self.sync = True
            else:
                self.period = period * period_units
                self.mean_motion = 2 * math.pi / self.period
                self.sync = False
        else:
            self.mean_motion = radial_speed
            self.period = 2 * math.pi / self.mean_motion / period_units
            self.sync = False
        self.epoch = epoch
        self.meridian_angle = meridian_angle * math.pi / 180

    def get_rotation_at(self, time):
        if self.sync:
            self.period, self.mean_motion = self.body.orbit.getPeriod()
        if self.period == 0:
            return LQuaterniond()
        angle = (time - self.epoch) * self.mean_motion + self.meridian_angle
        local = LQuaterniond()
        local.setFromAxisAngleRad(angle, LVector3d.unitZ())
        rotation = local * self.get_equatorial_rotation_at(time)
        return rotation
