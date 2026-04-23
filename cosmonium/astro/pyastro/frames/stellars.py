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

from panda3d.core import LQuaterniond

from .anchors import ReferenceFrame


class StellarAnchorReferenceFrame(ReferenceFrame):
    """Reference frame anchored to a stellar object with defined orbit and rotation."""

    def __init__(self, anchor=None):
        self.anchor = anchor

    def set_anchor(self, anchor):
        self.anchor = anchor

    def get_center(self):
        return self.anchor.get_local_position()

    def get_absolute_reference_point(self):
        return self.anchor.get_absolute_reference_point()

    def get_orientation(self):
        return LQuaterniond.ident_quat()

    def __str__(self):
        return self.__class__.__name__ + '(' + self.anchor.get_name() + ')'


class OrbitReferenceFrame(StellarAnchorReferenceFrame):
    def get_orientation(self):
        return self.anchor.orbit.frame.get_orientation()


class EquatorialReferenceFrame(StellarAnchorReferenceFrame):
    def get_orientation(self):
        return self.anchor.get_equatorial_rotation()


class SynchroneReferenceFrame(StellarAnchorReferenceFrame):
    def get_orientation(self):
        return self.anchor.get_sync_rotation()
