/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2022 Laurent Deru.
 *
 * Cosmonium is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Cosmonium is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Cosmonium.  If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef ASTRO_H
#define ASTRO_H

#include "math.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

const double m = 1.0 / 1000;
const double Km = 1.0;
const double AU = 149597870.700 * Km;
const double KmPerLy = 9460730472580.800;
const double Ly = KmPerLy * Km;
const double LyPerParsec = 3.26167;
const double Parsec = LyPerParsec * Ly;

const double KmPerParsec = LyPerParsec * KmPerLy;

const double abs_mag_distance = 10 * Parsec;

const double Day = 1.0;
const double Hour = Day / 24.0;
const double Min = Hour / 60.0;
const double Sec = Min / 60.0;
const double JYear = 365.25 * Day;
const double JCentury = JYear * 100.0;

const double J2000_Obliquity = 23.4392911;

// Factor to convert luminosity to magnitude
const double luminosity_magnitude_factor = log(10.0) / 2.5;

const double sun_abs_magnitude = 4.83;

const double sun_luminous_flux = 3.75e28;
const double sun_luminous_intensity = sun_luminous_flux / 4 / M_PI;

const double L0 = 3.0128e28;

const double radiance_coef =  L0 / (4 * M_PI * abs_mag_distance * abs_mag_distance / m / m);

inline double
to_rad(double deg)
{
  return deg / 180.0 * M_PI;
}

inline double
abs_to_app_mag(double abs_magnitude, double distance)
{
  // m = M + 5 * (log10(d) - 1)
  return abs_magnitude + 5 * (log10(distance / KmPerParsec) - 1);
}

inline double
app_to_abs_mag(double app_magnitude, double distance)
{
  // M = m - 5 * (log10(d) - 1)
  return app_magnitude - 5 * (log10(distance / KmPerParsec) - 1);
}

inline double
lum_to_abs_mag(double luminosity)
{
  // M* = M0 - 2.5 * log10(L* / L0)
  return sun_abs_magnitude - log(luminosity) / luminosity_magnitude_factor;
}
inline double
abs_mag_to_lum(double abs_magnitude)
{
  // L* = L0 * 10^((M0 - M*) / 2.5)
  return exp((sun_abs_magnitude - abs_magnitude) * luminosity_magnitude_factor);
}

inline double
radiance_to_mag(double radiance)
{
    if (radiance > 0) {
        return lum_to_abs_mag(radiance / radiance_coef);
    } else {
        return 1000.0;
    }
}

#endif
