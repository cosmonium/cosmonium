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


from panda3d.core import LQuaterniond, LVector3d

from ..parameters import ParametersGroup, UserParameter, AutoUserParameter

from ..astro.frame import J2000EquatorialReferenceFrame

from math import asin, atan2, pi

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
    def __init__(self, rotation, frame):
        Rotation.__init__(self, frame)
        self.rotation = rotation

    def get_user_parameters(self):
        group = Rotation.get_user_parameters(self)
        group.add_parameters(self.reference_axis.get_user_parameters())
        return group

    def update_user_parameters(self):
        self.reference_axis.update_user_parameters()

    def get_frame_equatorial_orientation_at(self, time):
        return self.rotation

    def get_frame_rotation_at(self, time):
        return self.rotation

class UnknownRotation(FixedRotation):
    def __init__(self):
        FixedRotation.__init__(self, LQuaterniond(), J2000EquatorialReferenceFrame())

class UniformRotation(Rotation):
    dynamic = True
    def __init__(self,
                 equatorial_orientation,
                 mean_motion,
                 meridian_angle,
                 epoch,
                 frame):
        Rotation.__init__(self, frame)
        self.equatorial_orientation = equatorial_orientation
        self.mean_motion = mean_motion
        self.epoch = epoch
        self.meridian_angle = meridian_angle

    def is_flipped(self):
        return self.mean_motion < 0

    def set_period(self, period):
        if period != 0:
            self.mean_motion = 2 * pi / period
        else:
            self.mean_motion = 0

    def get_period(self):
        return 2 * pi / self.mean_motion

    def get_frame_equatorial_orientation_at(self, time):
        return self.equatorial_orientation

    def get_frame_rotation_at(self, time):
        angle = (time - self.epoch) * self.mean_motion + self.meridian_angle
        local = LQuaterniond()
        if self.mean_motion < 0:
            angle = -angle
        local.setFromAxisAngleRad(angle, LVector3d.unitZ())
        rotation = local * self.get_frame_equatorial_orientation_at(time)
        return rotation

class SynchronousRotation(Rotation):
    def __init__(self,
                 equatorial_orientation,
                 meridian_angle,
                 epoch,
                 frame):
        Rotation.__init__(self, frame)
        self.equatorial_orientation = equatorial_orientation
        self.parent_body = None
        self.epoch = epoch
        self.meridian_angle = meridian_angle

    def set_parent_body(self, parent_body):
        self.parent_body = parent_body

    def get_parent_body(self):
        return self.parent_body

    def get_user_parameters(self):
        group = FixedRotation.get_user_parameters(self)
        group.add_parameter(AutoUserParameter(_("Meridian angle"), 'meridian_angle', self, UserParameter.TYPE_FLOAT, value_range=[-360, 360], units=pi / 180))
        group.add_parameter(AutoUserParameter(_("Epoch"), 'epoch', self, UserParameter.TYPE_FLOAT))
        return group

    def get_frame_equatorial_orientation_at(self, time):
        return self.equatorial_orientation

    def get_frame_rotation_at(self, time):
        angle = (time - self.epoch) * self.parent_body.orbit.get_mean_motion() + self.meridian_angle
        local = LQuaterniond()
        local.setFromAxisAngleRad(angle, LVector3d.unitZ())
        rotation = local * self.get_frame_equatorial_orientation_at(time)
        return rotation
