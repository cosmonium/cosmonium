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

#ifndef KEPLER_H
#define KEPLER_H

#include "pandabase.h"
#include "luse.h"

struct elements
{
   double perih_time, q, ecc, incl, arg_per, asc_node;
   double epoch,  mean_anomaly;
            /* derived quantities: */
   double lon_per, minor_to_major;
   double perih_vec[3], sideways[3];
   double angular_momentum, major_axis, t0, w0;
   double abs_mag, slope_param, gm;
   int is_asteroid, central_obj;
};

BEGIN_PUBLISH

LPoint3d
kepler_pos(const double pericenter, const double ecc, double mean_anom);

END_PUBLISH

void
setup_orbit_vectors(struct elements *e);

void
kepler_pos_vel(const struct elements *elem, const double t,
               double *loc, double *vel);

#endif //KEPLER_H
