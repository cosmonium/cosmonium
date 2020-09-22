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
from cosmonium.astro.frame import J2000EclipticReferenceFrame

try:
    from cosmonium_engine import gust86_sat_pos
    loaded = True
except ImportError as e:
    print("WARNING: Could not load GUST86 C implementation")
    print("\t", e)
    loaded = False

class Gust86(FuncOrbit):
    def __init__(self, sat_id, period, semi_major_axis, eccentricity):
        FuncOrbit.__init__(self, period, semi_major_axis, eccentricity, J2000EclipticReferenceFrame())
        self.sat_id = sat_id

    def is_periodic(self):
        return True

    def get_frame_position_at(self, time):
        return gust86_sat_pos(time, self.sat_id)

    def get_frame_rotation_at(self, time):
        return LQuaterniond()

orbit_elements_db.register_category('gust86', 100)
if loaded:
    orbit_elements_db.register_element('gust86', 'ariel',   Gust86(0,  2.520, 190900, 0.0012))
    orbit_elements_db.register_element('gust86', 'umbriel', Gust86(1,  4.144, 266000, 0.0039))
    orbit_elements_db.register_element('gust86', 'titania', Gust86(2,  8.706, 436300, 0.0011))
    orbit_elements_db.register_element('gust86', 'oberon',  Gust86(3, 13.46,  583500, 0.0014))
    orbit_elements_db.register_element('gust86', 'miranda', Gust86(4,  1.413, 129900, 0.0013))
