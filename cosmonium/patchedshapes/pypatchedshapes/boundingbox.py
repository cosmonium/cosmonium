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


import math
from panda3d.core import BoundingBox, LPoint3


class PatchBoundingBox:

    def __init__(self, points):
        self.points = points

    def create_bounding_volume(self, rot, offset):
        min_point = LPoint3(math.inf)
        max_point = LPoint3(-math.inf)
        for point in self.points:
            point = rot.xform(point + offset)
            for i in range(3):
                if point[i] < min_point[i]:
                    min_point[i] = point[i]
                if point[i] > max_point[i]:
                    max_point[i] = point[i]
        box = BoundingBox(min_point, max_point)
        return box

    def set_points(self, points):
        self.points = points

    def xform(self, mat):
        self.points = [mat.xform(point) for point in self.points]
