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
from cosmonium.astro.frame import J2000EquatorialReferenceFrame

try:
    from cosmonium_engine import rckin_sat_pos
    loaded = True
except ImportError as e:
    print("WARNING: Could not load RCKIN C implementation")
    print("\t", e)
    loaded = False

class Rckin(FuncOrbit):
    def __init__(self, sat_id, period, semi_major_axis, eccentricity):
        FuncOrbit.__init__(self, period, semi_major_axis, eccentricity, J2000EquatorialReferenceFrame())
        self.sat_id = sat_id

    def is_periodic(self):
        return True

    def get_frame_position_at(self, time):
        return rckin_sat_pos(time, self.sat_id)

    def get_frame_rotation_at(self, time):
        return LQuaterniond()

orbit_elements_db.register_category('rckin', 50)
if loaded:
    # Mars
    orbit_elements_db.register_element('rckin', 'phobos',   Rckin(401, 0.3189,  9376, 0.0151))
    orbit_elements_db.register_element('rckin', 'deimos',   Rckin(402, 1.2624, 23458, 0.0002))
    # Jupiter
    orbit_elements_db.register_element('rckin', 'amalthea', Rckin(505, 0.498, 181400, 0.0032))
    orbit_elements_db.register_element('rckin', 'thebe',    Rckin(514, 0.675, 221900, 0.0176))
    orbit_elements_db.register_element('rckin', 'adrastea', Rckin(515, 0.298, 129000, 0.0018))
    orbit_elements_db.register_element('rckin', 'metis',    Rckin(516, 0.295, 128000, 0.0012))
    # Saturn
    orbit_elements_db.register_element('rckin', 'janus',      Rckin(610, 0.695, 151450, 0.0098))
    orbit_elements_db.register_element('rckin', 'epimetheus', Rckin(611, 0.695, 151450, 0.0161))
    orbit_elements_db.register_element('rckin', 'helene',     Rckin(612, 2.737, 377444, 0.0000))
    orbit_elements_db.register_element('rckin', 'telesto',    Rckin(613, 1.888, 294720, 0.0002))
    orbit_elements_db.register_element('rckin', 'calypso',    Rckin(614, 1.888, 294721, 0.0005))
    orbit_elements_db.register_element('rckin', 'atlas',      Rckin(615, 0.602, 137774, 0.0011))
    orbit_elements_db.register_element('rckin', 'prometheus', Rckin(616, 0.613, 139429, 0.0022))
    orbit_elements_db.register_element('rckin', 'pandora',    Rckin(617, 0.629, 141810, 0.0042))
    orbit_elements_db.register_element('rckin', 'pan',        Rckin(618, 0.575, 133585, 0.0000))
    orbit_elements_db.register_element('rckin', 'daphnis',    Rckin(635, 0.594, 136504, 0.0000))
    # Uranus
    orbit_elements_db.register_element('rckin', 'cordelia',  Rckin(706, 0.335, 49800, 0.0003))
    orbit_elements_db.register_element('rckin', 'ophelia',   Rckin(707, 0.376, 53800, 0.0099))
    orbit_elements_db.register_element('rckin', 'bianca',    Rckin(708, 0.435, 59200, 0.0009))
    orbit_elements_db.register_element('rckin', 'cressida',  Rckin(709, 0.464, 61800, 0.0004))
    orbit_elements_db.register_element('rckin', 'desdemona', Rckin(710, 0.474, 62700, 0.0001))
    orbit_elements_db.register_element('rckin', 'juliet',    Rckin(711, 0.493, 64400, 0.0007))
    orbit_elements_db.register_element('rckin', 'portia',    Rckin(712, 0.513, 66100, 0.0001))
    orbit_elements_db.register_element('rckin', 'rosalind',  Rckin(713, 0.558, 69900, 0.0001))
    orbit_elements_db.register_element('rckin', 'belinda',   Rckin(714, 0.624, 75300, 0.0001))
    orbit_elements_db.register_element('rckin', 'puck',      Rckin(715, 0.762, 86000, 0.0001))
    orbit_elements_db.register_element('rckin', 'perdita',   Rckin(725, 0.638, 76417, 0.0116))
    orbit_elements_db.register_element('rckin', 'mab',       Rckin(726, 0.923, 97736, 0.0025))
    orbit_elements_db.register_element('rckin', 'cupid',     Rckin(727, 0.613, 74392, 0.0013))
    # Neptune
    orbit_elements_db.register_element('rckin', 'triton',   Rckin(801, 5.877, 354759, 0.0000))
    orbit_elements_db.register_element('rckin', 'naiad',    Rckin(803, 0.294,  48227, 0.0003))
    orbit_elements_db.register_element('rckin', 'thalassa', Rckin(804, 0.311,  50074, 0.0002))
    orbit_elements_db.register_element('rckin', 'despina',  Rckin(805, 0.335,  52526, 0.0002))
    orbit_elements_db.register_element('rckin', 'galatea',  Rckin(806, 0.429,  61953, 0.0001))
    orbit_elements_db.register_element('rckin', 'larissa',  Rckin(807, 0.555,  73548, 0.0014))
    orbit_elements_db.register_element('rckin', 'proteus',  Rckin(808, 1.122, 117646, 0.0005))
