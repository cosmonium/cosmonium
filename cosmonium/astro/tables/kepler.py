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

from ..orbits import FixedPosition, FixedOrbit, EllipticalOrbit, CircularOrbit
from ..frame import EquatorialReferenceFrame, J2000EquatorialReferenceFrame
from ..elementsdb import orbit_elements_db
from .. import units

kepler_orbits={}
celestia_orbits={}

kepler_orbits['sol-system']=FixedPosition(position=(0, 0, 0))

kepler_orbits['sun']=FixedOrbit()

kepler_orbits['earth']=EllipticalOrbit(
    semi_major_axis=1.0,
    eccentricity=0.0167,
    period=1.0,
    inclination=0.0001,
    ascending_node=348.739,
    long_of_pericenter=102.947,
    mean_longitude=100.464)

celestia_orbits['pluto']=EllipticalOrbit(
        semi_major_axis=39.54,
        eccentricity=0.24905,
        period=247.998,
        inclination=17.1405,
        ascending_node=110.299,
        arg_of_periapsis=113.834,
        mean_anomaly=14.53)

kepler_orbits['pluto']=EllipticalOrbit(
        semi_major_axis=2043.1,
        semi_major_axis_units=units.Km,
        eccentricity=0.003484,
        period=6.387206,
        period_units=units.Day,
        inclination=96.1680,
        ascending_node=223.0539,
        arg_of_periapsis=337.92,
        mean_longitude=77.960,
        frame=J2000EquatorialReferenceFrame())

orbit_elements_db.register_category('kepler', 0)
for (element_name, element) in kepler_orbits.items():
    orbit_elements_db.register_element('kepler', element_name, element)

orbit_elements_db.register_category('celestia', -1)
for (element_name, element) in celestia_orbits.items():
    orbit_elements_db.register_element('celestia', element_name, element)
