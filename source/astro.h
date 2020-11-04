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

#ifndef ASTRO_H
#define ASTRO_H

#include "math.h"

const double KmPerLy = 9460730472580.800;
const double LyPerParsec = 3.26167;

const double KmPerParsec = LyPerParsec * KmPerLy;

inline double
abs_to_app_mag(double abs_magnitude, double distance)
{
  return abs_magnitude + 5 * (log10(distance / KmPerParsec) - 1);
}

inline double
app_to_abs_mag(double app_magnitude, double distance)
{
  return app_magnitude - 5 * (log10(distance / KmPerParsec) - 1);
}

#endif
