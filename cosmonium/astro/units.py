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


from panda3d.core import LQuaterniond, LVector3d

from . import jdcal

from math import floor, pi

Km=1.0
m=Km/1000.0
AU=149597870.700 * Km
KmPerLy=9460730472580.800
Ly=KmPerLy * Km
mLy = Ly / 1000000.0
LyPerParsec = 3.26167
Parsec=LyPerParsec * Ly
KParsec = 1000 * Parsec
MParsec = 1000 * KParsec
GParsec = 1000 * MParsec
KmPerParsec=LyPerParsec * KmPerLy
c=299792.458

milky_way_radius = 100000 * Ly
earth_radius = 6378.140 * Km
neptune_radius = 24341 * Km
jupiter_radius = 71492 * Km
sun_radius = 695700 * Km

def toUnit(value, scales, extra=''):
    for scale in scales:
        if abs(value) >= scale[2]:
            value /= scale[1]
            return "%g%s %s" % (value, extra, scale[0])
    return "%g" % value

lengths_scale=[['Gpc', GParsec, GParsec / 10],
               ['Mpc', MParsec, MParsec / 10],
               ['Kpc', KParsec, KParsec / 10],
               ['ly', Ly, Ly / 10],
               ['au', AU, AU / 10],
               ['km', Km, Km],
               ['m', Km / 1000.0, 0]]

speeds_scale=[['Mpc/s', MParsec, MParsec / 10],
              ['Kpc/s', KParsec, KParsec / 10],
              ['ly/s', Ly, Ly / 100],
              ['c', c, c / 100],
              ['km/s', Km, Km],
              ['m/s', Km / 1000.0, 0]]

diameter_scale=[['Milky Way', milky_way_radius, milky_way_radius / 1000],
                ['Sun', sun_radius, jupiter_radius * 2],
                ['Jupiter', jupiter_radius, earth_radius * 6],
                ['Neptune', neptune_radius, earth_radius * 3],
                ['Earth', earth_radius, 0]]

Day=1.0
Hour=Day / 24.0
Min = Hour / 60.0
Sec = Min / 60.0
JYear=365.25 * Day
JCentury = JYear * 100.0

times_scale=[['Year', JYear, JYear],
             ['Day', Day, Day],
             ['Hour', Hour, Hour],
             ['Min', Min, Min],
             ['Sec', Sec, Sec]]

def time_to_values(time):
    (years, months, days, frac)=jdcal.jd2gcal(0, time)
    hours = int(frac * 24)
    mins = (frac * 24 * 60) % 60
    secs = (frac * 24 * 60 * 60) % 60
    return (years, months, days, hours, mins, secs)

def values_to_time(years, months, days, hours, mins, secs):
    (jd1, jd2) = jdcal.gcal2jd(years, months, days)
    frac = hours * 3600 + mins * 60 + secs
    frac /= 24.0 * 3600
    return jd1 + jd2 + frac

Rad=1.0
Deg=pi / 180.0
HourAngle=pi / 12.0

def degMinSec(d, m, s):
    if d >= 0.0:
        return (d + (m + s / 60.0) / 60.0)
    else:
        return (d - (m + s / 60.0) / 60.0)

def hourMinSec(h, m, s):
    return (h + (m + s / 60.0) / 60.0) * 15

def toDegMinSec(deg):
    d = floor(deg)
    m = floor((deg - d) * 60.0)
    s = (deg - d - m / 60.0) * 60.0 * 60.0
    return (d, m, s)

def toHourMinSec(deg):
    deg /= 15.0
    h = floor(deg)
    m = floor((deg - h) * 60.0)
    s = (deg - h - m / 60.0) * 60.0 * 60.0
    return (h, m, s)

def arcsec_to_rad(arcsec):
    return arcsec * pi / 180 / 3600

Deg_Per_Day = Deg / Day

J2000 = 2451545.0
J2000_Obliquity = 23.4392911

J200_EclipticOrientation = LQuaterniond()

J2000_Orientation = LQuaterniond()
J2000_Orientation.setFromAxisAngleRad(-J2000_Obliquity / 180.0 * pi, LVector3d.unitX())

J2000_GalacticNorthRightAscension = hourMinSec(12, 51, 26.282)
J2000_GalacticNorthDeclination = degMinSec(27, 7, 42.01)
J2000_GalacticCenterRightAscension = hourMinSec(17, 45, 37.224)
J2000_GalacticCenterDeclination = degMinSec(-28, 56, 10.23)
J2000_GalacticNode = 122.932

TropicalYear = 365.242198781 * Day
B1900 = 2415020.31352

J1BC = 1721057.5

def besselYearToJulian(byear):
    return (byear - 1900.0) * TropicalYear + B1900

sun_abs_magnitude = 4.83
sun_luminosity = 3.828e26
sun_power = 3.8462e26
sun_temperature=5780.0
L0 = 3.0128e28
