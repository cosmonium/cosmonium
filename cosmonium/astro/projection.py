#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2021 Laurent Deru.
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


from panda3d.core import LVector3d

from .astro import calc_orientation
from . import units

class InfinitePosition:
    def __init__(self, right_ascension, declination):
        self.right_ascension = right_ascension
        self.declination = declination
        self.orientation = calc_orientation(self.right_ascension, self.declination)

    def project(self, time, center, radius):
        position = self.orientation.xform(LVector3d(0, 0, radius))
        return units.J2000_Orientation.xform(position)
