#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2026 Laurent Deru.
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

# Coordinate System
# Panda3D Coordinate system : Z-Up Right-handed
#    x : right
#    y : forward (into screen)
#    z : up
# Mapped onto J2000.0 Ecliptic frame
#    x : vernal equinox
#    y :
#    z : North Pole
#
# Celestia and SpaceEngine are Y-Up Right-handed
#    Panda3d = Cel/SE
#      x    =    x
#      y    =    z
#      z    =   -y

from panda3d.core import LPoint3d, LQuaterniond

from ... import units


class ReferenceFrame:

    def get_center(self):
        raise NotImplementedError()

    def get_orientation(self):
        raise NotImplementedError()

    def get_absolute_reference_point(self):
        raise NotImplementedError()

    def get_absolute_position(self, frame_position):
        return self.get_absolute_reference_point() + self.get_local_position(frame_position)

    def get_local_position(self, frame_position):
        return self.get_center() + self.get_orientation().xform(frame_position)

    def get_frame_position(self, local_position):
        return self.get_orientation().conjugate().xform(local_position - self.get_center())

    def get_absolute_orientation(self, frame_orientation):
        return frame_orientation * self.get_orientation()

    def get_frame_orientation(self, absolute_orientation):
        return absolute_orientation * self.get_orientation().conjugate()

    def __str__(self):
        raise NotImplementedError()


class J2000BarycentricEclipticReferenceFrame(ReferenceFrame):
    def get_center(self):
        return LPoint3d()

    def get_orientation(self):
        return LQuaterniond()

    def get_absolute_reference_point(self):
        return LPoint3d()

    def get_local_position(self, frame_position):
        return frame_position

    def get_frame_position(self, local_position):
        return local_position

    def get_absolute_orientation(self, frame_orientation):
        return frame_orientation

    def get_frame_orientation(self, absolute_orientation):
        return absolute_orientation

    def __str__(self):
        return 'J2000BarycentricEclipticReferenceFrame'


class J2000BarycentricEquatorialReferenceFrame(ReferenceFrame):
    def get_center(self):
        return LPoint3d()

    def get_orientation(self):
        return units.J2000_Orientation

    def get_absolute_reference_point(self):
        return LPoint3d()

    def get_local_position(self, frame_position):
        return units.J2000_Orientation.xform(frame_position)

    def get_frame_position(self, local_position):
        return units.J2000_Orientation.conjugate().xform(local_position)

    def get_absolute_orientation(self, frame_orientation):
        return frame_orientation * units.J2000_Orientation

    def get_frame_orientation(self, absolute_orientation):
        return absolute_orientation * units.J2000_Orientation.conjugate()

    def __str__(self):
        return 'J2000BarycentricEquatorialReferenceFrame'
