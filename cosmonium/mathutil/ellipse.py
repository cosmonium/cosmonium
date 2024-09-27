#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2024 Laurent Deru.
#
# Cosmonium is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Cosmonium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#


# This file contains code from David Eberly, Geometric Tools, Redmond WA 98052
# https://www.geometrictools.com/
# This work is licensed under the Creative Commons Attribution 4.0 International License. To view a copy
# of this license, visit http://creativecommons.org/licenses/by/4.0/ or send a letter to Creative Commons,
# PO Box 1866, Mountain View, CA 94042, USA


from __future__ import annotations

from math import atan2, pi, sqrt, copysign

maxIter = 50
tol = 1.0e-19


def GetRoot(r0, z0, z1, g):
    n0 = r0 * z0
    s0 = z1 - 1
    if g < 0:
        s1 = 0
    else:
        s1 = sqrt(n0 * n0 + z1 * z1) - 1
    for _i in range(maxIter):
        s = (s0 + s1) / 2
        if s == s0 or s == s1:
            break
        ratio0 = n0 / (s + r0)
        ratio1 = z1 / (s + 1)
        g = ratio0 * ratio0 + ratio1 * ratio1 - 1
        if g > 0:
            s0 = s
        elif g < 0:
            s1 = s
        else:
            break
    return s


def DistancePointEllipse(e0: float, e1: float, y0i: float, y1i: float) -> tuple[float, float, float]:
    """
    returns the closest point on the surface of the ellipse to the given point and the distance between them.
    Note: It is required that e0 > e1
    :param e0: Major semi-axis of the ellipse
    :param e1: Minor semi-axis of the ellipse
    :param y0i: horizontal coordinate of the given point
    :param y1i: vertical coordinate of the given point
    :returns: Tuple containing the x coordinate and the y coordinate of the closest point on the surface
              and the distance to the given point.
    """
    y0 = abs(y0i)
    y1 = abs(y1i)
    if y1 > 0:
        if y0 > 0:
            z0 = y0 / e0
            z1 = y1 / e1
            g = z0 * z0 + z1 * z1 - 1
            if g != 0:
                r0 = (e0 / e1) * (e0 / e1)
                sbar = GetRoot(r0, z0, z1, g)
                x0 = r0 * y0 / (sbar + r0)
                x1 = y1 / (sbar + 1)
                distance = sqrt((x0 - y0) * (x0 - y0) + (x1 - y1) * (x1 - y1))
            else:
                x0 = y0
                x1 = y1
                distance = 0
        else:  # y0 == 0
            x0 = 0
            x1 = e1
            distance = abs(y1 - e1)
    else:  # y1 == 0
        numer0 = e0 * y0
        denom0 = e0 * e0 - e1 * e1
        if numer0 < denom0:
            xde0 = numer0 / denom0
            x0 = e0 * xde0
            x1 = e1 * sqrt(1 - xde0 * xde0)
            distance = sqrt((x0 - y0) * (x0 - y0) + x1 * x1)
        else:
            x0 = e0
            x1 = 0
            distance = abs(y0 - e0)
    x0 = copysign(x0, y0i)
    x1 = copysign(x1, y1i)
    return x0, x1, distance


def PointToGeodetic(ax: float, ay: float, xi: float, yi: float) -> tuple[float, float]:
    """
    Calculate the geodetic longitude, latitude and height of the given point wrt to the given ellipsoid
    Note: It is required that ax >= ay
    :param ax: X axis of the ellipse
    :param ay: Y axis of the ellipse
    :param xi: X coordinate of the given point
    :param yi: Y coordinate of the given point
    :return: A tuple with the geodetic latitude and the height
    """
    x = abs(xi)
    y = abs(yi)
    x2 = x * x
    y2 = y * y

    ax2 = ax * ax
    ay2 = ay * ay
    cz = ax2 / ay2

    # ----- Determination of foot point -----
    #       (using bisection method)

    if x == 0.0 and y == 0.0:
        sx = 0.0
        sy = 0.0
        m = 0.0
        # Mm = 0.0
    elif False and ay2 * x2 + ax2 * y2 < ax2 * ay2:
        sx = x
        sy = y
        m = 0.0
        # Mm = 0.0
    elif x == 0.0:
        sx = 0.0
        sy = ay
        m = 0.0
        # Mm = 0.0
    elif y == 0.0:
        sx = ax
        sy = 0.0
        m = 0.0
        # Mm = 0.0
    else:
        x0 = x / ax
        y0 = y / ay
        m, mMm = bisect2(x0, y0, tol, cz)
        sx = cz * x / (cz + m)
        sy = y / (1.0 + m)
    # Determination of latitude & longitude of foot point -----

    latitude = xyz2fl(ax, ay, sx, sy)

    # -Determination of geodetic height -----

    dx = x - sx
    dy = y - sy
    height = sqrt(dx * dx + dy * dy)

    if x + y < sx + sy:
        height = -height

    # Adjust latitude according to signs of (xi,yi)

    latitude = fl_octal(xi, yi, latitude)

    return latitude, height


def xyz2fl(e0, e1, y0, y1):
    # Computes the transformation of Cartesian to geodetic coordinates on the surface of the ellipsoid
    # assuming x,y,z are all non-negative
    # Angular coordinates in radians

    e = sqrt(e0 * e0 - e1 * e1) / e0
    theta = atan2(y1, y0 * (1.0 - e * e))
    return theta


def fl_octal(x, y, latitude):
    # Adjusts latitude according to signs of x,y (angles in radians)

    if y < 0.0:
        latitude = -latitude
    return latitude


def bisect2(x0, y0, tol, cz):
    #  Implements the bisection method on the X-Y plane

    n = 0
    m = -2.0
    d1 = y0 - 1.0
    g2 = cz * cz * x0 * x0
    d2 = sqrt(g2 + y0 * y0) - 1.0
    Gd = g2 / ((cz + d1) * (cz + d1))
    d = 0.50 * (d2 - d1)

    while d > tol:
        n += 1
        MC = m
        m = d1 + d
        Gm = (g2 / ((cz + m) * (cz + m))) + ((y0 * y0) / ((1.0 + m) * (1.0 + m))) - 1.0
        if MC == m + tol:
            return m, Gm
        if Gm == 0.0:
            return m, Gm
        else:
            if sign(Gm) == sign(Gd):
                d1 = m
                Gd = Gm
            else:
                d2 = m
        d = 0.50 * (d2 - d1)
    n += 1
    m = d1 + d
    Gm = (g2 / ((cz + m) * (cz + m))) + ((y0 * y0) / ((1.0 + m) * (1.0))) - 1.0

    return m, Gm


def sign(t):
    # Returns the sign of its argument
    if t > 0.0:
        n = 1
    elif t < 0.0:
        n = -1
    else:
        n = 0
    return n


def EllipseCircumRamanujan2ndApprox(a: float, b: float) -> float:
    try:
        h = pow(a - b, 2.0) / pow(a + b, 2.0)
    except ZeroDivisionError:
        return 0.0

    return pi * (a + b) * (1.0 + 3.0 * h / (10.0 + pow(4.0 - 3.0 * h, 0.5)))
