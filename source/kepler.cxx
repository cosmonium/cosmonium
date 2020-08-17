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

#include "math.h"

#include "kepler.h"

/* Significant parts of this code comes from Project Pluto library
 * by Bill Gray. See https://projectpluto.com/kepler.htm
 */

/* astfuncs.cpp: functions for asteroid/comet two-body ephems
Copyright (C) 2010, Project Pluto

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
02110-1301, USA.
*/

#define THRESH 1.e-12
#define MIN_THRESH 1.e-14
#define PI 3.141592653589793238462643383279502884197169399375105
#define CUBE_ROOT(X) (exp(log(X) / 3.0))

#define MAX_DEFAULT_ITERATIONS 7

#define MAX_ITERATIONS 20

static double
near_parabolic(const double ecc_anom, const double e)
{
  /* If the eccentricity is very close to parabolic,  and the eccentric
   anomaly is quite low,  you can get an unfortunate situation where
   roundoff error keeps you from converging.  Consider the just-barely-
   elliptical case,  where in Kepler's equation,
   M = E - e sin( E)
   E and e sin( E) can be almost identical quantities.  To
   around this,  near_parabolic( ) computes E - e sin( E) by expanding
   the sine function as a power series:
   E - e sin( E) = E - e( E - E^3/3! + E^5/5! - ...)
   = (1-e)E + e( -E^3/3! + E^5/5! - ...)
   It's a little bit expensive to do this,  and you only need do it
   quite rarely.  (I only encountered the problem because I had orbits
   that were supposed to be 'pure parabolic',  but due to roundoff,
   they had e = 1+/- epsilon,  with epsilon _very_ small.)  So 'near_parabolic'
   is only called if we've gone seven iterations without converging. */
  const double anom2 = (e > 1. ? ecc_anom * ecc_anom : -ecc_anom * ecc_anom);
  double term = e * anom2 * ecc_anom / 6.;
  double rval = (1. - e) * ecc_anom - term;
  unsigned n = 4;

  while (fabs(term) > 1e-15) {
    term *= anom2 / (double) (n * (n + 1));
    rval -= term;
    n += 2;
  }
  return (rval);
}

double
kepler_elliptic(const double ecc, double mean_anom)
{
  double curr, err, thresh, offset = 0.;
  double delta_curr = 1.0;
  bool is_negative = false;
  unsigned n_iter = 0;

  if (mean_anom == 0.0) {
    return 0.0;
  }

  if (mean_anom < -PI || mean_anom > PI) {
    double tmod = fmod(mean_anom, PI * 2.0);
    if (tmod > PI) { /* bring mean anom within -pi to +pi */
      tmod -= 2.0 * PI;
    } else if (tmod < -PI) {
      tmod += 2.0 * PI;
    }
    offset = mean_anom - tmod;
    mean_anom = tmod;
  }

  if (ecc < 0.9) {
    /* low-eccentricity formula from Meeus,  p. 195 */
    curr = atan2(sin(mean_anom), cos(mean_anom) - ecc);
    /* (usually) one or two correction steps,  and we're done */
    do {
      err = (curr - ecc * sin(curr) - mean_anom) / (1.0 - ecc * cos(curr));
      curr -= err;
    } while (fabs(err) > THRESH);
    return (curr + offset);
  }

  if (mean_anom < 0.0) {
    mean_anom = -mean_anom;
    is_negative = true;
  }

  curr = mean_anom;
  thresh = THRESH * fabs(1.0 - ecc);
  /* Due to roundoff error,  there's no way we can hope to */
  /* get below a certain minimum threshhold anyway:        */
  if (thresh < MIN_THRESH) {
    thresh = MIN_THRESH;
  }
  if (ecc > 0.8 && mean_anom < PI / 3.0) {
    /* up to 60 degrees */
    double trial = mean_anom / fabs(1.0 - ecc);
    if (trial * trial > 6.0 * fabs(1.0 - ecc)) {
      /* cubic term is dominant */
      trial = CUBE_ROOT(6.0 * mean_anom);
    }
    curr = trial;
    if (thresh > THRESH) {
      /* happens if e > 2. */
      thresh = THRESH;
    }
  }

  while (fabs(delta_curr) > thresh && n_iter < MAX_ITERATIONS) {
    if (n_iter > MAX_DEFAULT_ITERATIONS) {
      err = near_parabolic(curr, ecc) - mean_anom;
    } else {
      err = curr - ecc * sin(curr) - mean_anom;
    }
    delta_curr = -err / (1.0 - ecc * cos(curr));
    curr += delta_curr;
    n_iter += 1;
  }
  return (is_negative ? offset - curr : offset + curr);
}

double
kepler_parabolic(double mean_anom)
{
  double a = 3.0 / (2 * sqrt(2)) * mean_anom;
  double b = CUBE_ROOT(a + sqrt(a * a + 1));
  double true_anom = 2 * atan(b - 1 / b);
  return true_anom;
}

double
kepler_hyperbolic(const double ecc, double mean_anom)
{
  double curr, err, thresh = 0.0;
  double delta_curr = 1.0;
  bool is_negative = false;
  unsigned n_iter = 0;

  if (mean_anom == 0) {
    return 0.0;
  }

  if (mean_anom < 0.0) {
    mean_anom = -mean_anom;
    is_negative = true;
  }

  curr = mean_anom;
  thresh = THRESH * fabs(1.0 - ecc);
  /* Due to roundoff error,  there's no way we can hope to */
  /* get below a certain minimum threshold anyway:         */
  if (thresh < MIN_THRESH) {
    thresh = MIN_THRESH;
  }
  if (mean_anom / ecc > 3.0) {
    /* large-mean-anomaly */
    curr = log(mean_anom / ecc) + 0.85;
  } else {
    double trial = mean_anom / fabs(1.0 - ecc);

    if (trial * trial > 6. * fabs(1.0 - ecc)) {
      /* cubic term is dominant */
      trial = CUBE_ROOT(6. * mean_anom);
    }
    curr = trial;
    if (thresh > THRESH) {
      /* happens if e > 2. */
      thresh = THRESH;
    }
  }

  while (fabs(delta_curr) > thresh && n_iter < MAX_ITERATIONS) {
    if (n_iter > MAX_DEFAULT_ITERATIONS && ecc < 1.01) {
      err = -near_parabolic(curr, ecc) - mean_anom;
    } else {
      err = ecc * sinh(curr) - curr - mean_anom;
    }
    delta_curr = -err / (ecc * cosh(curr) - 1.0);
    curr += delta_curr;
    n_iter += 1;
  }
  return (is_negative ? - curr : curr);
}

LPoint3d
kepler_pos(const double pericenter, const double ecc, double mean_anom)
{
  if (ecc < 1.0) {
    double ecc_anom = kepler_elliptic(ecc, mean_anom);
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
    double ecc_anom = kepler_hyperbolic(ecc, mean_anom);
    double a = pericenter / (ecc - 1.0);
    double x = a * (ecc - cosh(ecc_anom) );
    double y = a * sqrt(ecc * ecc - 1) * sinh(ecc_anom);
    return LPoint3d(x, y, 0.0);
  }
}
