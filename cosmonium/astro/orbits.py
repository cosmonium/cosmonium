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

from panda3d.core import LPoint3d, LVector3d, LQuaterniond

from ..parameters import ParametersGroup, UserParameter, AutoUserParameter

from . import units
from .frame import J2000EquatorialReferenceFrame
from .kepler import kepler_pos
from .astro import calc_orientation

from math import pi, asin, atan2

class Orbit(object):
    dynamic = False
    def __init__(self, frame):
        self.frame = frame
        self.origin = LPoint3d()
        self.body = None

    def get_user_parameters(self):
        group = ParametersGroup(_('Orbit'))
        return group

    def update_user_parameters(self):
        pass

    def set_frame(self, frame):
        self.frame = frame

    def set_body(self, body):
        self.body = body

    def is_periodic(self):
        return False

    def is_closed(self):
        return False

    def get_period(self):
        return 0.0

    def get_mean_motion(self):
        return 0.0

    def get_global_position_at(self, time):
        return self.frame.get_absolute_reference_point()

    def get_frame_position_at(self, time):
        return None

    def get_frame_rotation_at(self, time):
        return None

    def get_position_at(self, time):
        return self.frame.get_local_position(self.get_frame_rotation_at(time).xform(self.get_frame_position_at(time)))

    def get_rotation_at(self, time):
        return self.frame.get_absolute_orientation(self.get_frame_rotation_at(time))

    def project(self, time, center, radius):
        return None

    def get_apparent_radius(self):
        return 0.0

class FixedPosition(Orbit):
    #TODO: Rename into something like GlobalFixedPosition
    def __init__(self, position=None, global_position=True,
                 right_asc=0.0, right_asc_unit=units.Deg,
                 declination=0.0, declination_unit=units.Deg,
                 distance=0.0, distance_unit=units.Ly,
                 frame=None):
        Orbit.__init__(self, frame)
        if position is None:
            self.right_asc = right_asc * right_asc_unit
            self.declination = declination * declination_unit
            distance = distance * distance_unit
        else:
            self.right_asc = None
            self.declination = None
            if not isinstance(position, LPoint3d):
                position = LPoint3d(*position)
        if position is None:
            self.orientation = calc_orientation(self.right_asc, self.declination)
            position = self.orientation.xform(LVector3d(0, 0, distance))
        if global_position:
            self.global_position = position
            self.position = LPoint3d()
        else:
            self.global_position = None
            self.position = position
        self.rotation=LQuaterniond()

    def get_global_position_at(self, time):
        if self.global_position is not None:
            return self.global_position
        else:
            return self.frame.get_absolute_reference_point()

    def set_frame_position(self, position):
        self.position = position

    def set_frame_rotation(self, rotation):
        self.rotation = rotation

    def get_frame_position_at(self, time):
        return self.position

    def get_frame_rotation_at(self, time):
        return self.rotation

    def calc_asc_decl(self):
        global_position = self.get_global_position_at(0)
        distance = global_position.length()
        if distance > 0:
            position = J2000EquatorialReferenceFrame.orientation.conjugate().xform(global_position)
            self.declination = asin(position[2] / distance)
            self.right_asc = atan2(position[1], position[0])
        else:
            self.right_asc = 0.0
            self.declination = 0.0

    def get_right_asc(self):
        if self.right_asc is None:
            self.calc_asc_decl()
        return self.right_asc

    def get_declination(self):
        if self.declination is None:
            self.calc_asc_decl()
        return self.declination

    def project(self, time, center, radius):
        vector = self.global_position - center
        vector /= vector.length()
        vector *= radius
        return vector

    def get_apparent_radius(self):
        return self.position.length()

class InfinitePosition(Orbit):
    def __init__(self,
                 right_asc=0.0, right_asc_unit=units.Deg,
                 declination=0.0, declination_unit=units.Deg,
                 frame=None):
        Orbit.__init__(self, frame)
        self.right_asc = right_asc * right_asc_unit
        self.declination = declination * declination_unit
        self.orientation = calc_orientation(self.right_asc, self.declination)
        self.position=LPoint3d()
        self.rotation=LQuaterniond()

    def project(self, time, center, radius):
        return self.orientation.xform(LVector3d(0, 0, radius))

    def get_frame_position_at(self, time):
        return self.position

    def get_frame_rotation_at(self, time):
        return self.rotation

class FixedOrbit(Orbit):
    def __init__(self, position=LPoint3d(0, 0, 0), rotation=LQuaterniond(), frame=None):
        Orbit.__init__(self, frame)
        self.position = position
        self.rotation = rotation

    def set_frame_position(self, position):
        self.position = position

    def set_frame_rotation(self, rotation):
        self.rotation = rotation

    def get_frame_position_at(self, time):
        return self.position

    def get_frame_rotation_at(self, time):
        return self.rotation

class EllipticalOrbit(Orbit):
    dynamic = True
    def __init__(self,
             pericenter_distance,
             period,
             eccentricity,
             inclination,
             ascending_node,
             arg_of_periapsis,
             mean_anomaly,
             epoch,
             frame):
        Orbit.__init__(self, frame)
        self.pericenter_distance = pericenter_distance
        self.apocenter_distance = pericenter_distance * (1.0 + eccentricity) / (1.0 - eccentricity)
        self.period = period
        self.mean_motion = 2 * pi / period
        self.eccentricity = eccentricity
        self.inclination = inclination * pi / 180
        self.ascending_node = ascending_node * pi / 180
        self.arg_of_periapsis = arg_of_periapsis * pi / 180
        self.mean_anomaly = mean_anomaly * pi / 180
        self.epoch = epoch
        self.update_rotation()

    def set_period(self, period):
        self.period = period
        if period != 0:
            self.mean_motion = 2 * pi / period
        else:
            self.mean_motion = 0

    def get_period(self):
        return self.period

    def update_rotation(self):
        inclination_quat = LQuaterniond()
        inclination_quat.setFromAxisAngleRad(self.inclination, LVector3d.unitX())
        arg_of_periapsis_quat = LQuaterniond()
        arg_of_periapsis_quat.setFromAxisAngleRad(self.arg_of_periapsis, LVector3d.unitZ())
        ascending_node_quat = LQuaterniond()
        ascending_node_quat.setFromAxisAngleRad(self.ascending_node, LVector3d.unitZ())
        self.rotation = arg_of_periapsis_quat * inclination_quat * ascending_node_quat

    def get_user_parameters(self):
        group = Orbit.get_user_parameters(self)
        group.add_parameters(
                      UserParameter(_("Period"), self.set_period, self.get_period, UserParameter.TYPE_FLOAT),
                      AutoUserParameter(_("Eccentricity"), "eccentricity", self, UserParameter.TYPE_FLOAT, value_range=[0, 10]),
                      AutoUserParameter(_("Inclination"), "inclination", self, UserParameter.TYPE_FLOAT, value_range=[-180, 180], units=pi / 180),
                      AutoUserParameter(_("Argument of periapsis"), 'arg_of_periapsis', self, UserParameter.TYPE_FLOAT, value_range=[-360, 360], units=pi / 180),
                      AutoUserParameter(_("Ascending node"), 'ascending_node', self, UserParameter.TYPE_FLOAT, value_range=[-360, 360], units=pi / 180),
                      AutoUserParameter(_("Mean anomaly"), 'mean_anomaly', self, UserParameter.TYPE_FLOAT, value_range=[-360, 360], units=pi / 180),
                      AutoUserParameter(_("Epoch"), 'epoch', self, UserParameter.TYPE_FLOAT),
                     )
        return group

    def update_user_parameters(self):
        self.update_rotation()

    def is_periodic(self):
        return self.eccentricity < 1.0

    def is_closed(self):
        return self.eccentricity < 1.0

    def get_mean_motion(self):
        return self.mean_motion

    def get_time_of_perihelion(self):
        return self.epoch - self.mean_anomaly / self.mean_motion

    def get_apparent_radius(self):
        return abs(self.apocenter_distance)

    def get_frame_position_at(self, time):
        mean_anomaly = (time - self.epoch) * self.mean_motion + self.mean_anomaly
        return kepler_pos(self.pericenter_distance, self.eccentricity, mean_anomaly)

    def get_frame_rotation_at(self, time):
        return self.rotation

class FuncOrbit(Orbit):
    dynamic = True
    def __init__(self, period, semi_major_axis, eccentricity, frame):
        self.period = period
        self.mean_motion = 2 * pi / period
        self.max_distance = semi_major_axis * (1.0 + eccentricity)
        self.frame = frame
        self.origin = LPoint3d()
        self.body = None

    def get_period(self):
        return self.period

    def get_mean_motion(self):
        return self.mean_motion

    def get_apparent_radius(self):
        return self.max_distance

def create_elliptical_orbit(semi_major_axis=None,
                            semi_major_axis_units=units.AU,
                            pericenter_distance=None,
                            pericenter_distance_units=units.AU,
                            mean_motion=None,
                            mean_motion_units=units.Deg_Per_Day,
                            period=None,
                            period_units=units.JYear,
                            eccentricity=0.0,
                            inclination=0,
                            ascending_node=0.0,
                            arg_of_periapsis=None,
                            long_of_pericenter=None,
                            mean_anomaly=None,
                            time_of_perihelion=None,
                            mean_longitude=0.0,
                            epoch = units.J2000,
                            frame=None):
    if pericenter_distance is None:
        if semi_major_axis is None:
            #TODO: raise error
            pericenter_distance = 1
        else:
            pericenter_distance = semi_major_axis  * semi_major_axis_units * (1.0 - eccentricity)
    else:
        pericenter_distance = pericenter_distance * pericenter_distance_units
    if period is None:
        if mean_motion is None:
            #TODO: raise error
            period = 0.0
        else:
            period = 2 * pi / (mean_motion * mean_motion_units)
    else:
        period = period * period_units
    if arg_of_periapsis is None:
        if long_of_pericenter is None:
            arg_of_periapsis = 0.0
        else:
            arg_of_periapsis = (long_of_pericenter - ascending_node) % 360.0
    if mean_anomaly is None:
        if mean_longitude is None:
            mean_anomaly = (epoch - time_of_perihelion) * (2 * pi / period) * 180 / pi
        else:
            mean_anomaly = (mean_longitude - (arg_of_periapsis + ascending_node)) % 360
    return EllipticalOrbit(pericenter_distance,
                           period,
                           eccentricity,
                           inclination,
                           ascending_node,
                           arg_of_periapsis,
                           mean_anomaly,
                           epoch,
                           frame)
