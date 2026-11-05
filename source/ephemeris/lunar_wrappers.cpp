/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2026 Laurent Deru.
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

#include "lunar_wrappers.h"

#include <math.h>

#include "lunar_raw.h"

#define PI 3.1415926535897932384626433832795028841971693993751058209749445923
#define AU_IN_KM 1.495978707e+8

static LPoint3d
spherical_to_cartesian(double lon, double lat, double r)
{
  return LPoint3d(cos(lon) * cos(lat) * r,
                  sin(lon) * cos(lat) * r,
                  sin(lat) * r);
}

static double
kepler_parabolic(double mean_anom)
{
  double a = 3.0 / (2 * sqrt(2)) * mean_anom;
  double b = exp(log(a + sqrt(a * a + 1)) / 3.0);
  return 2 * atan(b - 1 / b);
}

LPoint3d
kepler_pos(const double pericenter, const double ecc, double mean_anom)
{
  if (ecc < 1.0) {
    double ecc_anom = lunar_raw_kepler(ecc, mean_anom);
    double a = pericenter / (1.0 - ecc);
    double x = a * (cos(ecc_anom) - ecc);
    double y = a * sqrt(1 - ecc * ecc) * sin(ecc_anom);
    return LPoint3d(x, y, 0.0);
  } else if (ecc == 1.0) {
    double true_anom = kepler_parabolic(mean_anom);
    double r = 2 * pericenter / (1 + cos(true_anom));
    double x = r * cos(true_anom);
    double y = r * sin(true_anom);
    return LPoint3d(x, y, 0.0);
  } else {
    double ecc_anom = lunar_raw_kepler(ecc, mean_anom);
    double a = pericenter / (ecc - 1.0);
    double x = a * (ecc - cosh(ecc_anom) );
    double y = a * sqrt(ecc * ecc - 1) * sinh(ecc_anom);
    return LPoint3d(x, y, 0.0);
  }
}

LPoint3d
dourneau_sat_pos(double jd, int body)
{
  double loc[3];
  lunar_raw_dourneau(jd, body, loc);
  return LPoint3d(loc[0], loc[1], loc[2]) * AU_IN_KM;
}

LPoint3d
elp82_truncated_pos(double jd)
{
  double lon, lat, r;
  lunar_raw_elp82(jd, &lon, &lat, &r);
  return spherical_to_cartesian(lon * PI / 180., lat * PI / 180., r);
}

LPoint3d
gust86_sat_pos(double jd, int sat)
{
  double loc[3];
  lunar_raw_gust86(jd, sat, loc);
  return LPoint3d(loc[0], loc[1], loc[2]);
}

LPoint3d
htc20_sat_pos(double jd, int body)
{
  double loc[3];
  lunar_raw_htc20(jd, body, loc);
  return LPoint3d(loc[0] * AU_IN_KM, loc[1] * AU_IN_KM, loc[2] * AU_IN_KM);
}

LPoint3d
lieske_e5_sat_pos(double jd, int sat)
{
  double loc[3];
  lunar_raw_lieske_e5(jd, sat, loc);
  return LPoint3d(loc[0], loc[1], loc[2]);
}

LPoint3d
pluto_pos(double jd)
{
  double lon, lat, r;
  lunar_raw_pluto(jd, &lon, &lat, &r);
  return spherical_to_cartesian(lon, lat, r * AU_IN_KM);
}

LPoint3d
rckin_sat_pos(double jd, int body)
{
  double loc[3];
  lunar_raw_rock(jd, body, loc);
  return LPoint3d(loc[0], loc[1], loc[2]);
}

LPoint3d
vsop87_pos(double jd, int planet)
{
  double lon, lat, r;
  lunar_raw_vsop87(jd, planet, &lon, &lat, &r);
  return spherical_to_cartesian(lon, lat, r * AU_IN_KM);
}
