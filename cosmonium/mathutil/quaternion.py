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


from math import acos, sin, sqrt
from panda3d.core import LQuaterniond, LVector3d

from ..astro import units


def slerp(qa, qb, t):
    cosHalfTheta = qa.dot(qb)
    if cosHalfTheta < 0:
        cosHalfTheta = -cosHalfTheta
        qa = -qa
    if abs(cosHalfTheta) >= 1.0:
        return qa
    halfTheta = acos(cosHalfTheta)
    sinHalfTheta = sqrt(1.0 - cosHalfTheta * cosHalfTheta)
    if abs(sinHalfTheta) < 0.001:
        return (qa + qb) / 2
    ratioA = sin((1 - t) * halfTheta) / sinHalfTheta
    ratioB = sin(t * halfTheta) / sinHalfTheta
    return qa * ratioA + qb * ratioB


def quaternion_from_axis_angle(axis, angle, angle_units=units.Rad):
    if isinstance(axis, list):
        axis = LVector3d(*axis)
    axis.normalize()
    rot = LQuaterniond()
    rot.set_from_axis_angle_rad(angle * angle_units, axis)
    return rot


def quaternion_from_euler(h, p, r):
    rotation = LQuaterniond()
    rotation.set_hpr((h, p, r))
    return rotation


def relative_rotation(rotation, axis, angle):
    axis.normalize()
    rel_axis = rotation.xform(axis)
    delta_quat = LQuaterniond()
    try:
        delta_quat.set_from_axis_angle_rad(angle, rel_axis)
    except AssertionError:
        print("invalid axis", axis, axis.length(), rel_axis, rel_axis.length())
    return rotation * delta_quat
