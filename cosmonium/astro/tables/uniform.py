from __future__ import print_function
from __future__ import absolute_import

from ..frame import J2000EclipticReferenceFrame, EquatorialReferenceFrame

from ..rotations import UniformRotation
from ..elementsdb import rotation_elements_db

uniform_rotations={}

uniform_rotations['earth']=UniformRotation(
        period=23.93447117,
        inclination=-23.4392911,
        ascending_node=0,
        meridian_angle=280.147,
        frame=J2000EclipticReferenceFrame())

uniform_rotations['moon']=UniformRotation(
        right_asc=269.9949,
        declination=66.5392,
        meridian_angle=38.3213)

uniform_rotations['hyperion']=UniformRotation(
        inclination=61.0,
        period=120.0,
        ascending_node=145)

uniform_rotations['eris']=UniformRotation(
        period=25.92,
        inclination=79.8,
        ascending_node=144)

rotation_elements_db.register_category('uniform', 0)
for (element_name, element) in uniform_rotations.items():
    rotation_elements_db.register_element('uniform', element_name, element)
