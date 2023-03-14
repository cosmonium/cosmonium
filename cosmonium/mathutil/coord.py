from math import asin, atan2, cos, sin
from panda3d.core import LPoint3d


def cartesian_to_spherical(position):
    distance = position.length()
    if distance > 0:
        theta = asin(position[2] / distance)
        if position[0] != 0.0:
            phi = atan2(position[1], position[0])
            #Offset phi by 180 deg with proper wrap around
            #phi = (phi + pi + pi) % (2 * pi) - pi
        else:
            phi = 0.0
    else:
        phi = 0.0
        theta = 0.0
    return (phi, theta, distance)


def spherical_to_cartesian(position):
    (phi, theta, distance) = position
    #Offset phi by 180 deg with proper wrap around
    #phi = (phi + pi + pi) % (2 * pi) - pi
    rel_position = LPoint3d(cos(theta) * cos(phi), cos(theta) * sin(phi), sin(theta))
    rel_position *= distance
    return rel_position
