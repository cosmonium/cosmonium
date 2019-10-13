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

from ..frame import J2000EclipticReferenceFrame, EquatorialReferenceFrame
from .. import units
from ..rotations import create_uniform_rotation
from ..elementsdb import rotation_elements_db

uniform_rotations={}
uniform_rotations['earth']=create_uniform_rotation(
        period=23.93447117,
        inclination=-23.4392911,
        ascending_node=0,
        meridian_angle=280.147,
        frame=J2000EclipticReferenceFrame())

uniform_rotations['moon']=create_uniform_rotation(
        right_asc=269.9949,
        declination=66.5392,
        meridian_angle=38.3213)

uniform_rotations['hyperion']=create_uniform_rotation(
        inclination=61.0,
        period=120.0,
        ascending_node=145)

uniform_rotations['eris']=create_uniform_rotation(
        period=25.92,
        inclination=79.8,
        ascending_node=144)

rotation_elements_db.register_category('uniform', 0)
for (element_name, element) in uniform_rotations.items():
    rotation_elements_db.register_element('uniform', element_name, element)
