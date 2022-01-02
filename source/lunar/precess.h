/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2020 Laurent Deru.
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

#ifndef PRECESS_H
#define PRECESS_H

int
setup_ecliptic_precession(double *matrix, const double year_from, const double year_to);

int
setup_precession(double *matrix, const double year_from, const double year_to);

int
setup_precession_with_nutation(double *matrix, const double year);

void
equatorial_to_ecliptic(double *vect);

void
ecliptic_to_equatorial(double *vect);

int
precess_vector(const double *matrix,
               const double *v1,
               double *v2);

int
deprecess_vector(const double *matrix,
                 const double *v1,
                 double *v2);

int
precess_ra_dec(const double *matrix,
               double *p_out,
               const double *p_in,
               int backward);

#endif //PRECESS_H
