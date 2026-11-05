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

#ifndef LUNAR_RAW_H
#define LUNAR_RAW_H

/*
 * Thin layer over the 'lunar' library from Project Pluto (third-party/lunar).
 * It is the only place where the headers of the library are included as
 * they define macros (FAR, DLL_FUNC...) that conflict with Panda3D headers.
 *
 * All returned positions are relative to the central body, in the units of the underlying theory.
 */

/* Saturn satellites (Dourneau), ecliptic of date, position in AU */
int lunar_raw_dourneau(double jd, int body, double *xyz);

/* Moon (truncated ELP82): ecliptic of date, longitude and latitude in degrees, distance in km */
void lunar_raw_elp82(double jd, double *lon, double *lat, double *dist);

/* Uranus satellites (GUST86): J2000 equatorial, position in km */
void lunar_raw_gust86(double jd, int body, double *xyz);

/* Helene, Telesto and Calypso (HTC20), position in AU */
int lunar_raw_htc20(double jd, int body, double *xyz);

/* Galilean satellites (Lieske E5): ecliptic of date, position in km */
int lunar_raw_lieske_e5(double jd, int body, double *xyz);

/* Pluto (Meeus): ecliptic of date, longitude and latitude in radians, distance in AU */
int lunar_raw_pluto(double jd, double *lon, double *lat, double *dist);

/* Minor satellites ("rocks"): J2000 equatorial, position in km */
int lunar_raw_rock(double jd, int jpl_id, double *xyz);

/* Planets (VSOP87): ecliptic of date, longitude and latitude in radians, distance in AU */
void lunar_raw_vsop87(double jd, int planet, double *lon, double *lat, double *dist);

/* Solution of Kepler's equation for elliptic and hyperbolic orbits */
double lunar_raw_kepler(double ecc, double mean_anom);

#endif //LUNAR_RAW_H
