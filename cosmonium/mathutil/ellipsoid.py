#
# This file is part of Cosmonium.
#
# Copyright (C) 2018-2023 Laurent Deru.
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


# Code for Cartesian to geodetic coordinate conversion
# Authors: Panou & Korakitis, 2019
# Manuscript: "Cartesian to geodetic coordinates conversion on a triaxial ellipsoid using the bisection method"


from __future__ import annotations

from panda3d.core import LVector3d
from math import atan, cos, pi, sin, sqrt, copysign

from .ellipse import DistancePointEllipse

maxIter = 50
tol = 1.0e-19


def GetRoot(r0, r1, z0, z1, z2, g):
    n0 = r0 * z0
    n1 = r1 * z1
    s0 = z2 - 1
    if g < 0:
        s1 = 0
    else:
        s1 = sqrt(n0 * n0 + n1 * n1 + z2 * z2) - 1
    s = 0
    for i in range(maxIter):
        s = (s0 + s1) / 2
        if s == s0 or s == s1:
            break
        ratio0 = n0 / (s + r0)
        ratio1 = n1 / (s + r1)
        ratio2 = z2 / (s + 1)
        g = ratio0 * ratio0 + ratio1 * ratio1 + ratio2 * ratio2 - 1
        if g > 0:
            s0 = s
        elif g < 0:
            s1 = s
        else:
            break
    return s


def DistancePointEllipsoid(
        e0: float, e1: float, e2: float, y0i: float, y1i: float, y2i: float) -> tuple[float, float, float, float]:
    """
    returns the closest point on the surface of the ellipsoid to the given point and the distance between them.
    Note: It is required that e0 >= e1 >= e2
    :param e0: X axis of the ellipse
    :param e1: Y axis of the ellipse
    :param e2: Z axis of the ellipse
    :param y0i: X coordinate of the given point
    :param y1i: Y coordinate of the given point
    :param y2i: Z coordinate of the given point
    :returns: Tuple containing the x, y and z coordinate of the closest point on the surface
              and the distance to the given point.
    """
    y0 = abs(y0i)
    y1 = abs(y1i)
    y2 = abs(y2i)
    if y2 > 0:
        if y1 > 0:
            if y0 > 0:
                z0 = y0 / e0
                z1 = y1 / e1
                z2 = y2 / e2
                g = z0 * z0 + z1 * z1 + z2 * z2 - 1
                if g != 0:
                    r0 = (e0 / e2) * (e0 / e2)
                    r1 = (e1 / e2) * (e1 / e2)
                    sbar = GetRoot(r0, r1, z0, z1, z2, g)
                    x0 = r0 * y0 / (sbar + r0)
                    x1 = r1 * y1 / (sbar + r1)
                    x2 = y2 / (sbar + 1)
                    distance = sqrt((x0 - y0) * (x0 - y0) + (x1 - y1) * (x1 - y1) + (x2 - y2) * (x2 - y2))
                else:
                    x0 = y0
                    x1 = y1
                    x2 = y2
                    distance = 0
            else:  # y0==0
                x0 = 0
                x1, x2, distance = DistancePointEllipse(e1, e2, y1, y2)
        else:  # y1==0
            if y0 > 0:
                x1 = 0
                x0, x2, distance = DistancePointEllipse(e0, e2, y0, y2)
            else:  # y0==0
                x0 = 0
                x1 = 0
                x2 = e2
                distance = abs(y2 - e2)
    else:  # y2==0
        denom0 = e0 * 0 - e2 * e2
        denom1 = e1 * e1 - e2 * e2
        numer0 = e0 * y0
        numer1 = e1 * y1
        computed = False
        if numer0 < denom0 and numer1 < denom1:
            xde0 = numer0 / denom0
            xde1 = numer1 / denom1
            xde0sqr = xde0 * xde0
            xde1sqr = xde1 * xde1
            discr = 1 - xde0sqr - xde1sqr
            if discr > 0:
                x0 = e0 * xde0
                x1 = e1 * xde1
                x2 = e2 * sqrt(discr)
                distance = sqrt((x0 - y0) * (x0 - y0) + (x1 - y1) * (x1 - y1) + x2 * x2)
                computed = True
        if not computed:
            x2 = 0
            x0, x1, distance = DistancePointEllipse(e0, e1, y0, y1)
    x0 = copysign(x0, y0i)
    x1 = copysign(x1, y1i)
    x2 = copysign(x2, y2i)
    return x0, x1, x2, distance


def TriaxialGeodeticToCartesian(axes: LVector3d, long: float, lat: float, h: float) -> LVector3d:
    """
    Computes the geodetic coordinates from the given cartesian coordinates
    :param long: Longitude
    :param lat: Latitude
    :param h: Height from reference surface
    :returns: The cartesian position
    """
    ax2 = axes[0] * axes[0]
    ay2 = axes[1] * axes[1]
    b2 = axes[2] * axes[2]

    Ex2 = ax2 - b2
    Ee2 = ax2 - ay2
    lex2 = Ex2 / ax2
    lee2 = Ee2 / ax2
    mex = 1.0 - lex2
    mee = 1.0 - lee2

    ps = sin(lat)
    pc = cos(lat)
    ls = sin(long)
    lc = cos(long)

    D = 1.0 - lex2 * ps * ps - lee2 * pc * pc * ls * ls
    N = axes[0] / sqrt(D)

    pos = LVector3d(
        (N + h) * pc * lc,
        (N * mee + h) * pc * ls,
        (N * mex + h) * ps)
    return pos


def PointToTriaxialGeodetic(
        ax: float, ay: float, b: float, xi: float, yi: float, zi: float) -> tuple[float, float, float]:
    """
    Calculate the geodetic longitude, latitude and height of the given point wrt to the given ellipsoid
    Note: It is required that e0 >= e1 >= e2
    :param e0: X axis of the ellipse
    :param e1: Y axis of the ellipse
    :param e2: Z axis of the ellipse
    :param xi: X coordinate of the given point
    :param yi: Y coordinate of the given point
    :param zi: Z coordinate of the given point
    :return: A tuple with the geodetic longitude, latitude and the height
    """
    x = abs(xi)
    y = abs(yi)
    z = abs(zi)
    x2 = x * x
    y2 = y * y

    ax2 = ax * ax
    ay2 = ay * ay
    b2 = b * b
    Ex2 = ax2 - b2
    kx = Ex2 / ax
    ky = (ay2 - b2) / ay
    kx2 = kx * kx
    ky2 = ky * ky
    cx = ax2 / b2
    cy = ay2 / b2
    cz = ax2 / ay2

    # ----- Determination of foot point -----
    #       (using bisection method)

    if z == 0.0:
        if x == 0.0 and y == 0.0:
            sx = 0.0
            sy = 0.0
            sz = b
            m = 0.0
            Mm = 0.0
        elif ky2 * x2 + kx2 * y2 < kx2 * ky2:
            sx = ax * x / kx
            sy = ay * y / ky
            sz = b * sqrt(1.0 - (x2 / kx2) - (y2 / ky2))
            m = 0.0
            Mm = 0.0
        elif x == 0.0:
            sx = 0.0
            sy = ay
            sz = 0.0
            m = 0.0
            Mm = 0.0
        elif y == 0.0:
            sx = ax
            sy = 0.0
            sz = 0.0
            m = 0.0
            Mm = 0.0
        else:
            x0 = x / ax
            y0 = y / ay
            m, mMm = bisect2(x0, y0, tol, cz)
            sx = cz * x / (cz + m)
            sz = 0.0
            sy = y / (1.0 + m)
    else:
        if x == 0.0 and y == 0.0:
            sx = 0.0
            sy = 0.0
            sz = b
            m = 0.0
            Mm = 0.0
        else:
            x0 = x / ax
            y0 = y / ay
            z0 = z / b
            m, Mm = bisect3(x0, y0, z0, tol, cx, cy)
            sx = cx * x / (cx + m)
            sy = cy * y / (cy + m)
            if m < 0.0 and (ky2 * x2 + kx2 * y2) < kx2 * ky2:
                sz = b * sqrt(1.0 - ((sx * sx) / ax2) - ((sy * sy) / ay2))
            else:
                sz = z / (1.0 + m)
    # Determination of latitude & longitude of foot point -----

    longitude, latitude = xyz2fl(ax, ay, b, sx, sy, sz)

    # -Determination of geodetic height -----

    dx = x - sx
    dy = y - sy
    dz = z - sz
    height = sqrt(dx * dx + dy * dy + dz * dz)

    if x + y + z < sx + sy + sz:
        height = -height

    # Adjust latitude & longitude according to signs of (xi,yi,zi)

    longitude, latitude = fl_octal(xi, yi, zi, latitude, longitude)

    return longitude, latitude, height


def xyz2fl(ax, ay, b, x, y, z):
    # Computes the transformation of Cartesian to geodetic coordinates on the surface of the ellipsoid
    # assuming x,y,z are all non-negative
    # Angular coordinates in radians

    ax2 = ax * ax
    ay2 = ay * ay
    b2 = b * b
    Ex2 = ax2 - b2
    Ee2 = ax2 - ay2
    lex2 = Ex2 / ax2
    lee2 = Ee2 / ax2
    mex = 1.0 - lex2
    mee = 1.0 - lee2

    nom = mee * z
    xme = mee * x
    dex = xme * xme + y * y
    den = mex * sqrt(dex)
    rot = sqrt(dex)

    if den == 0.0:
        latitude = pi / 2.0
        longitude = 0.0
    else:
        if nom <= den:
            latitude = atan(nom / den)
        else:
            latitude = pi / 2.0 - atan(den / nom)
        if y <= xme:
            den = xme + rot
            longitude = 2.*atan(y / den)
        else:
            den = y + rot
            longitude = pi / 2.0 - 2.0 * atan(xme / den)
    return longitude, latitude


def fl_octal(x, y, z, latitude, longitude):
    # Adjusts latitude & longitude according to signs of x,y,z  (angles in radians)

    if z < 0.0:
        latitude = -latitude
    if x >= 0.0:
        if y < 0.0:
            longitude = -longitude
    else:
        if y >= 0.0:
            longitude = pi - longitude
        else:
            longitude = longitude - pi
    return longitude, latitude


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


def bisect3(x0, y0, z0, tol, cx, cy):
    # Implements the bisection method in 3D space

    n = 0
    m = -2.
    d1 = z0 - 1.0
    g2 = cx * cx * x0 * x0
    g3 = cy * cy * y0 * y0
    d2 = sqrt(g2 + g3 + z0 * z0) - 1.0
    Hd = g2 / ((cx + d1) * (cx + d1)) + g3 / ((cy + d1) * (cy + d1))
    d = 0.50 * (d2 - d1)

    while d > tol:
        n += 1
        MC = m
        m = d1 + d
        Hm = (g2 / ((cx + m) * (cx + m))) + (g3 / ((cy + m) * (cy + m))) + ((z0 * z0) / ((1.0 + m) * (1.0 + m))) - 1.0
        if MC == m + tol:
            return m, Hm
        if Hm == 0.0:
            return m, Hm
        else:
            if sign(Hm) == sign(Hd):
                d1 = m
                Hd = Hm
            else:
                d2 = m
        d = 0.50 * (d2 - d1)
    n += 1
    m = d1 + d
    Hm = (g2 / ((cx + m) * (cx + m))) + (g3 / ((cy + m) * (cy + m))) + ((z0 * z0) / ((1.0 + m) * (1.0 + m))) - 1.0

    return m, Hm


def sign(t):
    # Returns the sign of its argument
    if t > 0.0:
        n = 1
    elif t < 0.0:
        n = -1
    else:
        n = 0
    return n
