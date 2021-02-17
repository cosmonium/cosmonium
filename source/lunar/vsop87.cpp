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

#include "math.h"

#include "vsop87.h"
#include "vsop_data.h"

/* vsopson.cpp: functions for medium-precision planetary coordinates

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

#include <stdint.h>
#include <assert.h>

#include "lunar.h"

/* This function,  given a pointer to a buffer containing the data from
VSOP.BIN,  can compute planetary positions in heliocentric ecliptic
coordinates.  'planet' can run from 0=sun,  1=mercury,  ... 8=neptune.
(VSOP doesn't handle the moon or Pluto.)  'value' can be either
0=ecliptic longitude, 1=ecliptic latitude, 2=distance from sun.
(These are ecliptic coordinates _of date_,  by the way!)

   t = (JD - 2451545.) / 36525. = difference from J2000,  in Julian
centuries. 'prec' ('precision') can be used to tell the code to ignore
small terms in the VSOP expansion.  Once upon a time,  when math
coprocessors were rare,  I occasionally made use of this fact.  Nowadays,
almost all my code sets prec=0 (i.e.,  include all terms.)

   This function relies on direct reading of binary data.   See
'get_bin.h' for details on this. */

double calc_vsop_loc(const void *data, const int planet,
                     const int value, double t, double prec)
{
   int16_t *loc;
   int i, j;
   double sum, rval = 0., power = 1.;
   double *tptr;

   if(!planet) {
      return(0.);       /* the sun */
   }

   assert(planet > 0 && planet < 9);
   assert(value >= 0 && value <= 2);
   assert(data);                         /* now check VSOP data is correct */
   assert(((char *)data)[2] == '&');     /* verify a few bytes at random   */
   assert(((char *)data)[20] == 'x');
   assert(((char *)data)[0xea0a] == 'q');
   assert(get16bits((char *)data + 0x10c) == 0x93e);
   t /= 10.;         /* convert to julian millennia */
   loc = (int16_t *)data + (planet - 1) * 18 + value * 6;
   for(i = 6; i; i--, loc++)
   {
      const int16_t loc0 = get16bits(loc);
      const int16_t loc1 = get16bits(loc + 1);

      assert(loc0 >= 0);
      assert(loc1 >= loc0);
      assert(loc1 <= 0x97e);
      sum = 0.;
      if( prec < 0.) {
         prec = -prec;
      }
      tptr = (double *)((int16_t *)data + 8 * 18 + 1) + loc0 * 3U;

      for (j = loc1 - loc0; j; j--, tptr += 3)
      {
         const double amplitude = get_double(tptr);

         if (amplitude > prec || amplitude < -prec)
         {
            const double argument =
                             get_double(tptr + 1) + get_double(tptr + 2) * t;

            sum += amplitude * cos(argument);
         }
      }
      rval += sum * power;
      power *= t;
      if (t != 0.) {
         prec /= t;
      }
   }

   if (((char *)data)[2] == 38) {
      rval *= 1.e-8;
   }
   if (value == 0)   /* ensure 0 < lon < 2 * pi  */
   {
      rval = fmod(rval, TWO_PI);
      if (rval < 0.) {
         rval += TWO_PI;
      }
   }
   return(rval);
}

LPoint3d
vsop87_pos(double jd, int planet)
{
  double tc = (jd - J2000) / CENTURY;
  double lon = calc_vsop_loc((void *)vsop_data, planet, 0, tc, 0);
  double lat = calc_vsop_loc((void *)vsop_data, planet, 1, tc, 0);
  double r = calc_vsop_loc((void *)vsop_data, planet, 2, tc, 0);
  r *= AU_IN_KM;

  return LPoint3d(cos(lon) * cos(lat) * r,
                  sin(lon) * cos(lat) * r,
                  sin(lat) * r);
}
