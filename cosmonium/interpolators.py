#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2020 Laurent Deru.
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

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from .heightmapshaders import HeightmapDataSource

class Interpolator:
    def get_data_source_interpolator(self):
        raise NotImplementedError()

class HardwareInterpolator(Interpolator):
    def get_data_source_interpolator(self):
        return HeightmapDataSource.I_Hardware

class SoftwareInterpolator(Interpolator):
    def get_data_source_interpolator(self):
        return HeightmapDataSource.I_Software
