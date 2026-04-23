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


from panda3d.core import LQuaterniond, LVector3d

from ... import units
from ...astro import calc_orientation
from .base import ReferenceFrame


class AnchorReferenceFrame(ReferenceFrame):
    def __init__(self, anchor=None):
        self.anchor = anchor

    def set_anchor(self, anchor):
        self.anchor = anchor

    def get_center(self):
        return self.anchor.get_local_position()

    def get_orientation(self):
        return self.anchor.get_absolute_orientation()

    def get_absolute_reference_point(self):
        return self.anchor.get_absolute_reference_point()

    def __str__(self):
        return self.__class__.__name__ + '(' + self.anchor.body.get_name() + ')'


class J2000EclipticReferenceFrame(AnchorReferenceFrame):
    _orientation = LQuaterniond()

    def get_orientation(self):
        return self._orientation


class J2000EquatorialReferenceFrame(AnchorReferenceFrame):

    def get_orientation(self):
        return units.J2000_Orientation


class CelestialReferenceFrame(AnchorReferenceFrame):
    """
    Reference frame built using the North pole axis (ra, decl) and the
    longitude at the node, where the perpendicular plane intersects the
    equatorial plane.
    """

    def __init__(
        self,
        anchor=None,
        right_ascension=0.0,
        declination=0.0,
        longitude_at_node=0.0,
    ):
        AnchorReferenceFrame.__init__(self, anchor)
        self.right_ascension = right_ascension
        self.declination = declination
        self.longitude_at_node = longitude_at_node

        longitude_quad = LQuaterniond()
        longitude_quad.setFromAxisAngleRad(self.longitude_at_node, LVector3d.unitZ())
        self.orientation = (
            longitude_quad * calc_orientation(self.right_ascension, self.declination, False) * units.J2000_Orientation
        )

    def get_orientation(self):
        return self.orientation
