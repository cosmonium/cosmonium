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

from ..elementsdb import orbit_elements_db

try:
    from cosmonium_engine import LieskeE5Orbit
    loaded = True
except ImportError as e:
    print("WARNING: Could not load Lieske E5 C implementation")
    print("\t", e)
    loaded = False

orbit_elements_db.register_category('e5', 100)
if loaded:
    orbit_elements_db.register_element('e5', 'io',       LieskeE5Orbit(0,  1.769,  421800, 0.0041))
    orbit_elements_db.register_element('e5', 'europa',   LieskeE5Orbit(1,  3.551,  671100, 0.0094))
    orbit_elements_db.register_element('e5', 'ganymede', LieskeE5Orbit(2,  7.155, 1070400, 0.0013))
    orbit_elements_db.register_element('e5', 'callisto', LieskeE5Orbit(3, 16.69,  1882700, 0.0074))
