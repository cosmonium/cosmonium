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

#ifndef MATHUTILS_H
#define MATHUTILS_H

double
acose(const double arg);

double
asine(const double arg);

void
set_identity_matrix(double *matrix);

void
invert_orthonormal_matrix(double *matrix);

void
rotate_vector(double *v, const double angle, const int axis);

void
pre_spin_matrix(double *v1, double *v2, const double angle);

void spin_matrix(double *v1, double *v2, const double angle);

void
polar3_to_cartesian(double *vect, const double lon, const double lat);

double
vector3_length(const double *vect);

void
vector_cross_product(double *xprod, const double *a, const double *b);

#endif //MATHUTILS_H
