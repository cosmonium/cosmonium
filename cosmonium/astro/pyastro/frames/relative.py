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

from .base import ReferenceFrame


class RelativeReferenceFrame(ReferenceFrame):
    def __init__(self, parent_frame, position, orientation):
        ReferenceFrame.__init__(self)
        self.parent_frame = parent_frame
        self.frame_position = position
        self.frame_orientation = orientation

    def get_center(self):
        return self.parent_frame.get_local_position(self.frame_position)

    def get_orientation(self):
        return self.parent_frame.get_absolute_orientation(self.frame_orientation)

    def get_absolute_reference_point(self):
        return self.parent_frame.get_absolute_reference_point()

    def __str__(self):
        return self.__class__.__name__ + '(' + str(self.parent_frame) + ')'
