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

#include "precess.h"

/* precess.cpp: functions for computing Earth precession

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
02110-1301, USA.    */

/* This implements the IAU1976 precession model,  in two forms.
'setup_equatorial_precession_from_j2000()' sets up a precession matrix in
equatorial coordinates.  It appears that this is the preferred method in
most cases,  especially when doing full modelling of earth orientation
parameters (EOP) with observed offsets included.

   setup_ecliptic_precession_from_j2000() sets up the same sort of matrix,
but in ecliptic coordinates.  In the ecliptic reference frame,  precession
is (almost entirely) just a rotation around the ecliptic pole;  doing it
in equatorial coordinates is a poor fit to the actual physics.

   That led me to examine the actual formulae,  and sure enough,  the cubic
terms for equatorial precession are 600 or more times larger in magnitude
than those for equatorial precession.  Thus,  those oversized cubic terms
become huge as one goes a hundred centuries or so into the past or future.
(If you animate the earth's polar motion using this method,  you see the
earth's pole do most of a complete precession circle around the ecliptic
pole;  then it just goes wandering off as the cubic term diverges.)  In the
ecliptic frame,  the same terms are almost negligible.

   However,  the two methods lead to slightly different results.  The
discrepancy is zero at J2000 (where both methods provide identity matrices),
and of about a nanoradian every three years as one gets away for J2000.
(This corresponds to a difference in the earth's orientation of about
one centimeter every five years.)  For long-term stability,  I'd recommend
the ecliptic method.  But for very precise earth orientation in the near
term,  you're sort of stuck with having to use the equatorial method.
Which is why both are provided below.

   As originally given,  the formulae provide a way to create precession
matrices to go directly from any time t1 to another time t2.  The problem
I saw with this was that if you then generated a matrix to go from t2
to t1,  it wouldn't be the inverse of the first matrix.  That seemed wrong.
(In practice,  precessing and "de-precessing" a point got you very close
to your original point,  but it wasn't a perfect recovery,  and got worse
for longer time spans.)

   Therefore,  the following creates precession matrices from J2000 to
a given time,  using the setup_ecliptic_precession_from_j2000( ) function.
If you want to go from a given time to J2000,  the same function is
called and the result is inverted.  If you want to go from a time t1
to a time t2,  the code creates a J2000-to-t1 matrix and inverts it.
(Fortunately,  we're talking about orthonormal matrices;  inversion is
simply transposition.)  Then it makes a J2000-to-t2 matrix,  and
multiplies the two matrices. (With some logic to skip some steps if
t1=2000 or t2=2000,  where you'd get identity matrices anyway.)  Thus,
precession and inverse precession are exactly inverse operations.    */

#include <math.h>
#include <string.h>
#include "lunar.h"
#include "mathutils.h"
#include "obliquity.h"

static int
setup_ecliptic_precession_from_j2000(double *matrix, const double year)
{
   const double t = (year - 2000.) / 100.;
   const double S2R = (PI / 180.) / 3600.;   /* converts arcSeconds to Radians */
   const double eta = t * (47.0029 * S2R + (-.03302 * S2R + 6.e-5 * S2R * t) * t);
   const double pie = 174.876384 * PI / 180. -
           t * (869.8089 * S2R - .03536 * S2R * t);
   const double p = t * (5029.0966 * S2R + (1.11113 * S2R - 6.e-5 * S2R * t) * t);

   set_identity_matrix( matrix);
#ifdef UNNECESSARY_MATH
   spin_matrix(matrix, matrix + 3, -pie);
#else       /* can get the same result without as much math: */
   matrix[0] = matrix[4] = cos( pie);
   matrix[1] = sin( pie);
   matrix[3] = -matrix[1];
#endif
   spin_matrix(matrix + 3, matrix + 6, -eta);
   spin_matrix(matrix + 3, matrix, -p);
   spin_matrix(matrix, matrix + 3, pie);
   return (0);
}

static int
setup_equatorial_precession_from_j2000(double *matrix, const double year)
{
   const double t_cen = (year - 2000.) / 100.;
   const double ka = 2306.2181;
   const double kb = 2004.3109;
   const double arcsec_to_radians = (PI / 180.) / 3600.;
   double zeta, z, theta, czeta, cz, ctheta, szeta, sz, stheta;

   zeta  = t_cen * (ka + t_cen * ( .30188 + .017998 * t_cen)) * arcsec_to_radians;
   z     = t_cen * (ka + t_cen * (1.09468 + .018203 * t_cen)) * arcsec_to_radians;
   theta = t_cen * (kb + t_cen * (-.42665 - .041833 * t_cen)) * arcsec_to_radians;
   czeta = cos( zeta);
   szeta = sin( zeta);
   cz = cos( z);
   sz = sin( z);
   ctheta = cos( theta);
   stheta = sin( theta);

   *matrix++ = czeta * ctheta * cz - szeta * sz;
   *matrix++ = -szeta * ctheta * cz - czeta * sz;
   *matrix++ = -stheta * cz;

   *matrix++ = czeta * ctheta * sz + szeta * cz;
   *matrix++ = -szeta * ctheta * sz + czeta * cz;
   *matrix++ = -stheta * sz;

   *matrix++ = czeta * stheta;
   *matrix++ = -szeta * stheta;
   *matrix++ = ctheta;

   return( 0);
}

#define SEMIRANDOM_GARBAGE1  314.8145501e+12
#define SEMIRANDOM_GARBAGE2  -9.19001473e-08

int
setup_ecliptic_precession(double *matrix, const double year_from, const double year_to)
{
   int rval;
         /* It's pretty common to precess a few zillion data points.  So   */
         /* it helps to cache the most recently computed precession matrix */
         /* so that repeated calls don't result in repeated computation.   */
   static double prev_year_from = SEMIRANDOM_GARBAGE1;
   static double prev_year_to   = SEMIRANDOM_GARBAGE2;
   static double prev_matrix[9];

   if (fabs(year_from - year_to) < 1.e-5)   /* dates sensibly equal; */
   {                                        /* avoid pointless math */
      set_identity_matrix( matrix);
      return( 0);
   }

   if (year_from == prev_year_from && year_to == prev_year_to)
   {
      memcpy(matrix, prev_matrix, 9 * sizeof(double));
      return (0);
   }
               /* Similarly,  it's common to precess first  */
               /* in one direction,  then the other:        */
   if(year_from == prev_year_to && year_to == prev_year_from)
   {
      memcpy(matrix, prev_matrix, 9 * sizeof( double));
      invert_orthonormal_matrix(matrix);
      return (0);
   }
               /* OK,  this is definitely something new: */
   if(year_from == 2000.)
   {
      rval = setup_ecliptic_precession_from_j2000(matrix, year_to);
   }
   else
   {
      rval = setup_ecliptic_precession_from_j2000(matrix, year_from);
      invert_orthonormal_matrix(matrix);
      if (year_to != 2000.)
      {
         double product[9], tmatrix[9];
         int i, j;

         setup_ecliptic_precession_from_j2000(tmatrix, year_to);
         for (i = 0; i < 3; i++)
         {
            for (j = 0; j < 3; j++)
            {
               product[j + i * 3] = matrix[i * 3    ] * tmatrix[j]
                                  + matrix[i * 3 + 1] * tmatrix[j + 3]
                                  + matrix[i * 3 + 2] * tmatrix[j + 6];
            }
         }
         memcpy(matrix, product, 9 * sizeof(double));
      }
   }
               /* Store matrix for likely subsequent use: */
   memcpy(prev_matrix, matrix, 9 * sizeof( double));
   prev_year_from = year_from;
   prev_year_to = year_to;
   return (rval);
}

int
setup_precession(double *matrix, const double year_from, const double year_to)
{
   const double obliquity1 = mean_obliquity((year_from - 2000.) / 100.);
   const double obliquity2 = mean_obliquity((year_to - 2000.) / 100.);

   setup_ecliptic_precession(matrix, year_from, year_to);
   pre_spin_matrix(matrix + 1, matrix + 2, obliquity1);
   spin_matrix(matrix + 3, matrix + 6, obliquity2);
   return (0);
}

static const double sin_obliq_2000 = 0.397777155931913701597179975942380896684;
static const double cos_obliq_2000 = 0.917482062069181825744000384639406458043;

void
equatorial_to_ecliptic(double *vect)
{
   double temp;

   temp    = vect[2] * cos_obliq_2000 - vect[1] * sin_obliq_2000;
   vect[1] = vect[1] * cos_obliq_2000 + vect[2] * sin_obliq_2000;
   vect[2] = temp;
}

void
ecliptic_to_equatorial(double *vect)
{
   double temp;

   temp    = vect[2] * cos_obliq_2000 + vect[1] * sin_obliq_2000;
   vect[1] = vect[1] * cos_obliq_2000 - vect[2] * sin_obliq_2000;
   vect[2] = temp;
}

int
precess_vector(const double *matrix,
               const double *v1,
               double *v2)
{
   int i = 3;

   while (i--)
   {
      *v2++ = matrix[0] * v1[0] + matrix[1] * v1[1] + matrix[2] * v1[2];
      matrix += 3;
   }
   return( 0);
}

int
deprecess_vector(const double *matrix,
                 const double *v1,
                 double *v2)
{
   int i = 3;

   while (i--)
   {
      *v2++ = matrix[0] * v1[0] + matrix[3] * v1[1] + matrix[6] * v1[2];
      matrix++;
   }
   return (0);
}

int
precess_ra_dec(const double *matrix,
               double *p_out,
               const double *p_in,
               int backward)
{
   double v1[3], v2[3];
   const double old_ra = p_in[0];

   v1[0] = cos(p_in[0]) * cos(p_in[1]);
   v1[1] = sin(p_in[0]) * cos(p_in[1]);
   v1[2] =                sin(p_in[1]);
   if (backward)
      deprecess_vector(matrix, v1, v2);
   else
      precess_vector(matrix, v1, v2);
   if (v2[1] != 0. || v2[0] != 0.)
      p_out[0] = atan2(v2[1], v2[0]);
   else
      p_out[0] = 0.;
   p_out[1] = asine(v2[2]);
   while (p_out[0] - old_ra > PI)
      p_out[0] -= PI * 2.;
   while (p_out[0] - old_ra <-PI)
      p_out[0] += PI * 2.;
   return (0);
}
