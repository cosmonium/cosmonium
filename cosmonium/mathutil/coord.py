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


from math import asin, atan2, cos, sin
from panda3d.core import LPoint3d


def cartesian_to_spherical(position):
    distance = position.length()
    if distance > 0:
        theta = asin(position[2] / distance)
        if position[0] != 0.0:
            phi = atan2(position[1], position[0])
            # Offset phi by 180 deg with proper wrap around
            # phi = (phi + pi + pi) % (2 * pi) - pi
        else:
            phi = 0.0
    else:
        phi = 0.0
        theta = 0.0
    return (phi, theta, distance)


def spherical_to_cartesian(position):
    (phi, theta, distance) = position
    # Offset phi by 180 deg with proper wrap around
    # phi = (phi + pi + pi) % (2 * pi) - pi
    rel_position = LPoint3d(cos(theta) * cos(phi), cos(theta) * sin(phi), sin(theta))
    rel_position *= distance
    return rel_position
