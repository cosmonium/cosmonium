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
#but WITHOUT ANY WARRANTY without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#

from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import LPoint3d

from math import sqrt, cos, sin, fabs, pi, atan2, exp, log, fmod, atan, sinh, cosh

THRESH = 1.0e-12
MIN_THRESH = 1.0e-14

MAX_DEFAULT_ITERATIONS = 7
MAX_ITERATIONS = 20

def CUBE_ROOT(X):
    return exp(log(X) / 3.0)

def near_parabolic(ecc_anom, e):
    if e > 1.0:
        anom2 = ecc_anom * ecc_anom
    else:
        anom2 = -ecc_anom * ecc_anom
    term = e * anom2 * ecc_anom / 6.0
    rval = (1.0 - e) * ecc_anom - term
    n = 4
    while fabs(term) > 1e-15:
        term *= anom2 / (n * (n + 1))
        rval -= term
        n += 2
    return rval

def kepler_elliptic(ecc, mean_anom):
    curr = 0.0
    err = 0.0
    offset = 0.0
    delta_curr = 1.0
    is_negative = False
    n_iter = 0

    if (mean_anom == 0.0):
        return 0.0

    if mean_anom < -pi or mean_anom > pi:
        tmod = fmod(mean_anom, pi * 2.0)
        if tmod > pi:
            tmod -= 2.0 * pi
        elif tmod < -pi:
            tmod += 2.0 * pi
        offset = mean_anom - tmod
        mean_anom = tmod

    if ecc < 0.9:
        curr = atan2(sin(mean_anom), cos(mean_anom) - ecc)
        err = THRESH + THRESH
        while fabs(err) > THRESH:
            err = (curr - ecc * sin(curr) - mean_anom) / (1.0 - ecc * cos(curr))
            curr -= err
        return curr + offset

    if mean_anom < 0.0:
        mean_anom = -mean_anom
        is_negative = True

    curr = mean_anom
    thresh = THRESH * fabs(1.0 - ecc)
    if thresh < MIN_THRESH:
        thresh = MIN_THRESH

    if ecc > 0.8 and mean_anom < pi / 3.0:
        trial = mean_anom / fabs(1.0 - ecc)
        if (trial * trial > 6.0 * fabs(1.0 - ecc)):
            trial = CUBE_ROOT(6.0 * mean_anom)
        curr = trial
        if thresh > THRESH:
            thresh = THRESH

    while fabs(delta_curr) > thresh and n_iter < MAX_ITERATIONS:
        if n_iter > MAX_DEFAULT_ITERATIONS:
            err = near_parabolic(curr, ecc) - mean_anom
        else:
            err = curr - ecc * sin(curr) - mean_anom

        delta_curr = -err / (1.0 - ecc * cos(curr))
        curr += delta_curr
        n_iter += 1

    if is_negative:
        return offset - curr
    else:
        return offset + curr

def kepler_parabolic(mean_anom):
    a = 3.0 / (2 * sqrt(2)) * mean_anom
    b = CUBE_ROOT(a + sqrt(a * a + 1))
    true_anom = 2 * atan(b - 1 / b)
    return true_anom

def kepler_hyperbolic(ecc, mean_anom):
    err = 0.0
    delta_curr = 1.0
    is_negative = False
    n_iter = 0

    if mean_anom == 0:
        return 0.0

    if mean_anom < 0.0:
        mean_anom = -mean_anom
        is_negative = True

    curr = mean_anom
    thresh = THRESH * fabs(1.0 - ecc)
    if thresh < MIN_THRESH:
        thresh = MIN_THRESH

    if mean_anom / ecc > 3.0:
        curr = log(mean_anom / ecc) + 0.85
    else:
        trial = mean_anom / fabs(1.0 - ecc)
        if trial * trial > 6. * fabs(1.0 - ecc):
            trial = CUBE_ROOT(6. * mean_anom)
        curr = trial
        if thresh > THRESH:
            thresh = THRESH

    while fabs(delta_curr) > thresh and n_iter < MAX_ITERATIONS:
        if n_iter > MAX_DEFAULT_ITERATIONS and ecc < 1.01:
            err = -near_parabolic(curr, ecc) - mean_anom
        else:
            err = ecc * sinh(curr) - curr - mean_anom
        delta_curr = -err / (ecc * cosh(curr) - 1.0)
        curr += delta_curr
        n_iter += 1
    if is_negative:
        return -curr
    else:
        return curr

def kepler_pos(pericenter, ecc, mean_anom):
    if (ecc < 1.0):
        ecc_anom = kepler_elliptic(ecc, mean_anom)
        a = pericenter / (1.0 - ecc)
        x = a * (cos(ecc_anom) - ecc)
        y = a * sqrt(1 - ecc * ecc) * sin(ecc_anom)
        return LPoint3d(x, y, 0.0)
    elif ecc == 1.0:
        true_anom = kepler_parabolic(mean_anom)
        r = 2 * pericenter / (1 + cos(true_anom))
        x = r * cos(true_anom)
        y = r * sin(true_anom)
        return LPoint3d(x, y, 0.0)
    else:
        ecc_anom = kepler_hyperbolic(ecc, mean_anom)
        a = pericenter / (ecc - 1.0)
        x = a * (ecc - cosh(ecc_anom) )
        y = a * sqrt(ecc * ecc - 1) * sinh(ecc_anom)
        return LPoint3d(x, y, 0.0)
