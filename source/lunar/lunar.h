/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2019 Laurent Deru.
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

#ifndef LUNAR_H
#define LUNAR_H

#define PI 3.1415926535897932384626433832795028841971693993751058209749445923
#define TWO_PI (PI + PI)

#define AU_IN_KM 1.495978707e+8

#define J2000 2451545.
#define J1900 (J2000 - 36525.)

#define OBLIQUITY_1950 (23.445792 * PI / 180.)
#define OBLIQUITY_2000 (23.43929111111111 * PI / 180.)

#define CENTURY 36525.

#define DEG2RAD (PI / 180.)

#define ARCSECONDS_TO_RADIANS (DEG2RAD / 3600.)

#define get16bits(d)  (*((const uint16_t *) (d)))
#define get32bits(d)  (*((const uint32_t *) (d)))
#define get64bits(d)  (*((const uint64_t *) (d)))

#define get16sbits(d)  (*((const int16_t *) (d)))
#define get32sbits(d)  (*((const int32_t *) (d)))
#define get64sbits(d)  (*((const int64_t *) (d)))

#define get_double(d) (*((const double *) (d)))

#endif /* LUNAR_H */
