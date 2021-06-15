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


from ..elementsdb import orbit_elements_db

try:
    from cosmonium_engine import HTC20Orbit
    loaded = True
except ImportError as e:
    print("WARNING: Could not load HTC20 C implementation")
    print("\t", e)
    loaded = False

orbit_elements_db.register_category('htc20', 100)
if loaded:
    orbit_elements_db.register_element('htc20', 'helene',  HTC20Orbit(0, 2.737, 377444, 0.0000))
    orbit_elements_db.register_element('htc20', 'telesto', HTC20Orbit(1, 1.888, 294720, 0.0002))
    orbit_elements_db.register_element('htc20', 'calypso', HTC20Orbit(2, 1.888, 294721, 0.0005))
