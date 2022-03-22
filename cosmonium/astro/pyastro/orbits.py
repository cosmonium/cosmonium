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


from panda3d.core import LPoint3d, LVector3d, LQuaterniond

from ...parameters import ParametersGroup, UserParameter, AutoUserParameter
from ..kepler import kepler_pos

from math import pi

class Orbit(object):
    def __init__(self, frame):
        self.frame = frame

    def get_user_parameters(self):
        group = ParametersGroup(_('Orbit'))
        return group

    def update_user_parameters(self):
        pass

    def set_frame(self, frame):
        self.frame = frame

    def is_periodic(self):
        raise NotImplementedError()

    def is_closed(self):
        raise NotImplementedError()

    def is_dynamic(self):
        raise NotImplementedError()

    def get_absolute_reference_point_at(self, time):
        return self.frame.get_absolute_reference_point()

    def get_absolute_position_at(self, time):
        return self.frame.get_absolute_reference_point() + self.get_local_position_at(time)

    def get_local_position_at(self, time):
        return self.frame.get_local_position(self.get_frame_rotation_at(time).xform(self.get_frame_position_at(time)))

    def get_frame_position_at(self, time):
        return None

    def get_absolute_rotation_at(self, time):
        return self.frame.get_absolute_orientation(self.get_frame_rotation_at(time))

    def get_frame_rotation_at(self, time):
        return None

    def get_bounding_radius(self):
        return 0.0

class FixedPosition(Orbit):
    def is_periodic(self):
        return False

    def is_closed(self):
        return False

    def is_dynamic(self):
        return False

class AbsoluteFixedPosition(FixedPosition):
    def __init__(self, frame, absolute_reference_point):
        FixedPosition.__init__(self, frame)
        self.absolute_reference_point = absolute_reference_point

    def get_absolute_reference_point_at(self, time):
        return self.absolute_reference_point

    def get_frame_position_at(self, time):
        return LPoint3d()

    def get_frame_rotation_at(self, time):
        return LQuaterniond()

class LocalFixedPosition(FixedPosition):
    def __init__(self, frame, frame_position, frame_rotation=LQuaterniond()):
        FixedPosition.__init__(self, frame)
        self.frame_position = frame_position
        self.frame_rotation = frame_rotation

    def set_frame_position(self, position):
        self.frame_position = position

    def set_frame_rotation(self, rotation):
        self.frame_rotation = rotation

    def get_frame_position_at(self, time):
        return self.frame_position

    def get_frame_rotation_at(self, time):
        return self.frame_rotation

class EllipticalOrbit(Orbit):
    def __init__(self,
             frame,
             epoch,
             mean_motion,
             mean_anomaly,
             pericenter_distance,
             eccentricity,
             argument_of_periapsis,
             inclination,
             ascending_node):
        Orbit.__init__(self, frame)
        self.pericenter_distance = pericenter_distance
        self.apocenter_distance = pericenter_distance * (1.0 + eccentricity) / (1.0 - eccentricity)
        self.period = 2 * pi / mean_motion
        self.mean_motion = mean_motion
        self.eccentricity = eccentricity
        self.inclination = inclination
        self.ascending_node = ascending_node
        self.argument_of_periapsis = argument_of_periapsis
        self.mean_anomaly = mean_anomaly
        self.epoch = epoch
        self.update_rotation()

    def is_dynamic(self):
        return True

    def is_closed(self):
        return True

    def is_periodic(self):
        return self.eccentricity < 1.0

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
        argument_of_periapsis_quat = LQuaterniond()
        argument_of_periapsis_quat.setFromAxisAngleRad(self.argument_of_periapsis, LVector3d.unitZ())
        ascending_node_quat = LQuaterniond()
        ascending_node_quat.setFromAxisAngleRad(self.ascending_node, LVector3d.unitZ())
        self.rotation = argument_of_periapsis_quat * inclination_quat * ascending_node_quat

    def get_mean_motion(self):
        return self.mean_motion

    def get_time_of_perihelion(self):
        return self.epoch - self.mean_anomaly / self.mean_motion

    def get_bounding_radius(self):
        return abs(self.apocenter_distance)

    def get_frame_position_at(self, time):
        mean_anomaly = (time - self.epoch) * self.mean_motion + self.mean_anomaly
        return kepler_pos(self.pericenter_distance, self.eccentricity, mean_anomaly)

    def get_frame_rotation_at(self, time):
        return self.rotation

class FunctionOrbit(Orbit):
    pass
