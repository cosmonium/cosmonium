/* obliquit.cpp: function to compute earth's obliquity

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

/* 21 Sep 2011:  improved caching of previous values.  Also,  the
formula diverges badly outside +/- 10 millenia,  so I "capped"
results at that point.  The test code now compares to the IAU
obliquity formula,  and shows values linearly interpolated from
integrated values from a file due to Laskar.   */

#include "lunar.h"

#define CLIP_OBLIQUITY

          /* obliquity formula comes from p 135, Meeus,  Astro Algor */
          /* input is time in julian centuries from 2000. */
          /* rval is mean obliq. (epsilon sub 0) in radians */
          /* Valid range is the years -8000 to +12000 (t = -100 to 100) */

double
mean_obliquity(const double t_cen)
{
   double u, u0;
   unsigned i;
   const double obliquit_minus_100_cen = 24.232841111 * PI / 180.;
   const double obliquit_plus_100_cen =  22.611485556 * PI / 180.;
   static double j2000_obliquit = 23. * 3600. + 26. * 60. + 21.448;
   static double t0 = 30000., rval;
   static long coeffs[10] = { -468093L, -155L, 199925L, -5138L,
            -24967L, -3905L, 712L, 2787L, 579L, 245L };

   if (t_cen == 0.)      /* common J2000 case;  don't do any math */
      return( j2000_obliquit * ARCSECONDS_TO_RADIANS);
#ifdef CLIP_OBLIQUITY
   else if (t_cen > 100.)      /* Diverges outside +/- 10 millennia,  */
      return (obliquit_plus_100_cen);
   else if (t_cen < -100.)  /* so we might as well clip to that  */
      return (obliquit_minus_100_cen);
#endif

   if (t0 == t_cen)    /* return previous answer */
      return( rval);

   rval = j2000_obliquit;
   t0 = t_cen;
   u = u0 = t_cen / 100.;     /* u is in julian 10000's of years */
   for( i = 0; i < 10; i++, u *= u0)
   {
      rval += u * (double)coeffs[i] / 100.;
   }

   rval *= ARCSECONDS_TO_RADIANS;
   return (rval);
}
