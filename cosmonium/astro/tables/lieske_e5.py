#This file is part of Cosmonium.
#
#Copyright (C) 2018-2019 Laurent Deru.
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

from panda3d.core import LQuaterniond

from ..elementsdb import orbit_elements_db
from ..orbits import FuncOrbit

try:
    from cosmonium_engine import lieske_e5_sat_pos
    loaded = True
except ImportError as e:
    print("WARNING: Could not load Leske E5 C implementation")
    print("\t", e)
    loaded = False

class LieskE5(FuncOrbit):
    def __init__(self, sat_id, period, semi_major_axis, eccentricity):
        FuncOrbit.__init__(self, period, semi_major_axis, eccentricity)
        self.sat_id = sat_id

    def is_periodic(self):
        return True

    def get_frame_position_at(self, time):
        #TODO: The position is in the ecliptic plane of date, not J2000.0
        #The precession must be taken into account
        return lieske_e5_sat_pos(time, self.sat_id)

    def get_frame_rotation_at(self, time):
        return LQuaterniond()

orbit_elements_db.register_category('e5', 100)
if loaded:
    orbit_elements_db.register_element('e5', 'io',       LieskE5(0,  1.769,  421800, 0.0041))
    orbit_elements_db.register_element('e5', 'europa',   LieskE5(1,  3.551,  671100, 0.0094))
    orbit_elements_db.register_element('e5', 'ganymede', LieskE5(2,  7.155, 1070400, 0.0013))
    orbit_elements_db.register_element('e5', 'callisto', LieskE5(3, 16.69,  1882700, 0.0074))
