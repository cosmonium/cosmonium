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

#include "lunar_raw.h"

#include "watdefs.h"
#include "lunar.h"
#include "gust86.h"

#include "vsop_data.h"

#define J2000 2451545.
#define CENTURY 36525.
#define JRADIUS_IN_KM 71418.0
/* Value of the AU used by gust86_posn() to scale its output */
#define GUST86_AU_IN_KM 149597870.0

/* These two functions are not declared in the headers of the library */
int htc20(const double jd, const int sat_no, double *xyz, double *vxyz);
double kepler(const double ecc, double mean_anom);

int
lunar_raw_dourneau(double jd, int body, double *xyz)
{
  return calc_ssat_loc(jd, xyz, body, 0);
}

void
lunar_raw_elp82(double jd, double *lon, double *lat, double *dist)
{
  double fund[N_FUND];
  double tc = (jd - J2000) / CENTURY;

  lunar_fundamentals(vsop_data, tc, fund);
  *lat = lunar_lat(vsop_data, fund, 0L);
  lunar_lon_and_dist(vsop_data, fund, lon, dist, 0L);
}

void
lunar_raw_gust86(double jd, int body, double *xyz)
{
  double loc[6];
  gust86_posn(jd, body, loc);
  xyz[0] = loc[0] * GUST86_AU_IN_KM;
  xyz[1] = loc[1] * GUST86_AU_IN_KM;
  xyz[2] = loc[2] * GUST86_AU_IN_KM;
}

int
lunar_raw_htc20(double jd, int body, double *xyz)
{
  return htc20(jd, body, xyz, 0);
}

int
lunar_raw_lieske_e5(double jd, int body, double *xyz)
{
  double loc[15];
  int result = calc_jsat_loc(jd, loc, 1 << body, 0);
  int i = body * 3;
  xyz[0] = loc[i + 0] * JRADIUS_IN_KM;
  xyz[1] = loc[i + 1] * JRADIUS_IN_KM;
  xyz[2] = loc[i + 2] * JRADIUS_IN_KM;
  return result;
}

int
lunar_raw_pluto(double jd, double *lon, double *lat, double *dist)
{
  double loc[3];
  double tc = (jd - J2000) / CENTURY;

  int result = calc_pluto_loc(vsop_data, loc, tc, 0);
  *lon = loc[0];
  *lat = loc[1];
  *dist = loc[2];
  return result;
}

int
lunar_raw_rock(double jd, int jpl_id, double *xyz)
{
  return evaluate_rock(jd, jpl_id, xyz);
}

void
lunar_raw_vsop87(double jd, int planet, double *lon, double *lat, double *dist)
{
  double tc = (jd - J2000) / CENTURY;
  *lon = calc_vsop_loc((void *)vsop_data, planet, 0, tc, 0);
  *lat = calc_vsop_loc((void *)vsop_data, planet, 1, tc, 0);
  *dist = calc_vsop_loc((void *)vsop_data, planet, 2, tc, 0);
}

double
lunar_raw_kepler(double ecc, double mean_anom)
{
  return kepler(ecc, mean_anom);
}
