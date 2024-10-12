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


def slerp(qa, qb, t):
    cosHalfTheta = qa.dot(qb)
    if cosHalfTheta < 0:
        cosHalfTheta = -cosHalfTheta
        qa = -qa
    if abs(cosHalfTheta) >= 1.0:
        return qa
    halfTheta = acos(cosHalfTheta)
    sinHalfTheta = sqrt(1.0 - cosHalfTheta*cosHalfTheta)
    if abs(sinHalfTheta) < 0.001:
        return (qa + qb) / 2
    ratioA = sin((1 - t) * halfTheta) / sinHalfTheta
    ratioB = sin(t * halfTheta) / sinHalfTheta
    return qa * ratioA + qb * ratioB
