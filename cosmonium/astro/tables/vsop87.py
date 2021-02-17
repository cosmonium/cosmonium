#
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
    from cosmonium_engine import VSOP87Orbit
    loaded = True
except ImportError as e:
    print("WARNING: Could not load VSOP87 C implementation")
    print("\t", e)
    loaded = False

orbit_elements_db.register_category('vsop87', 100)

if loaded:
    orbit_elements_db.register_element('vsop87', 'mercury', VSOP87Orbit(1,   0.2408467,   0.38709927, 0.20563593))
    orbit_elements_db.register_element('vsop87', 'venus',   VSOP87Orbit(2,   0.61519726,  0.72333566, 0.00677672))
    orbit_elements_db.register_element('vsop87', 'earth',   VSOP87Orbit(3,   1.0000174,   1.00000261, 0.01671123))
    orbit_elements_db.register_element('vsop87', 'mars',    VSOP87Orbit(4,   1.8808476,   1.52371034, 0.09339410))
    orbit_elements_db.register_element('vsop87', 'jupiter', VSOP87Orbit(5,  11.862615,    5.20288700, 0.04838624))
    orbit_elements_db.register_element('vsop87', 'saturn',  VSOP87Orbit(6,  29.447498,    9.53667594, 0.05386179))
    orbit_elements_db.register_element('vsop87', 'uranus',  VSOP87Orbit(7,  84.016846,   19.18916464, 0.04725744))
    orbit_elements_db.register_element('vsop87', 'neptune', VSOP87Orbit(8, 164.79132,    30.06992276, 0.00859048))
