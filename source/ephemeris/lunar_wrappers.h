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

#ifndef LUNAR_WRAPPERS_H
#define LUNAR_WRAPPERS_H

#include "pandabase.h"
#include "luse.h"

/*
 * Interrogate wrappers for the 'lunar' library, based on the lunar_raw interface.
 * Theses wrappers returns positions relative to the main body of the theory, in km.
 */

BEGIN_PUBLISH

LPoint3d
kepler_pos(double pericenter, double ecc, double mean_anom);

LPoint3d
dourneau_sat_pos(double jd, int body);

LPoint3d
elp82_truncated_pos(double jd);

LPoint3d
gust86_sat_pos(double jd, int body);

LPoint3d
htc20_sat_pos(double jd, int body);

LPoint3d
lieske_e5_sat_pos(double jd, int body);

LPoint3d
pluto_pos(double jd);

LPoint3d
rckin_sat_pos(double jd, int body);

LPoint3d
vsop87_pos(double jd, int planet);

END_PUBLISH

#endif //LUNAR_WRAPPERS_H
