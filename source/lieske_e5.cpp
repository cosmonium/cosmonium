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

#include "lieske_e5.h"

/* Significant parts of this code comes from Project Pluto library
 * by Bill Gray. See https://projectpluto.com/source.htm
 */

/* jsats.cpp: functions for Galilean satellite posns

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

/* The calc_jsat_loc( ) function in this file computes the positions
of the Galilean satellites.  The algorithm is straight out of Jean
Meeus' _Astronomical Algorithms_,  second edition;  he,  in turn,
got it from J. Lieske's E5 theory :

http://aas.aanda.org/articles/aas/pdf/1998/08/ds6503.pdf

   NOTE that I haven't included all the trig terms!

   A previous version of this code used Lieske's E2x3 theory,
straight from the first edition of _AA_.  About all that changed
were the coefficients.  I can't think of a good reason to use
the earlier version,  except maybe to see how much changed.  Let
me know if you want a copy of it.

   At some point,  this code should probably be replaced with the
L1.2 theory due to Lainey (2004).  Some discussion of this is at

ftp://ftp.imcce.fr/pub/ephem/satel/galilean/L1/L1.2/     */

#include <math.h>
#include <string.h>
#include "lunar.h"

#define COEFF2RAD (PI / 180.e+5)
#define PER (13.469942 * PI / 180.)
#define JRADIUS_IN_KM 71418.0

      /* This algorithm has a lot of angles which are linear functions */
      /* of time,  with the slope and offset expressed in degrees.  To */
      /* get a result properly converted to radians,  the following    */
      /* macro is useful:                                              */
#define LINEAR_FUNC(A, B, t) ((A * DEG2RAD) + (B * DEG2RAD) * t)

      /* And there are a few cubic functions of time,  too: */
#define CUBIC_FUNC(A, B, C, D, t) (A * DEG2RAD + t * (B * DEG2RAD \
                        + t * (C * DEG2RAD + D * DEG2RAD * t)))

static void rotate_vector(const double angle, double *x, double *y)
{
   const double sin_angle = sin(angle);
   const double cos_angle = cos(angle);
   const double temp = cos_angle * *x - sin_angle * *y;

   *y = sin_angle * *x + cos_angle * *y;
   *x = temp;
}

/* 28 Sep 2002:  Kazumi Akiyama pointed out two slightly wrong
   coefficients (marked 'KA fix' below).  These change the position
   of Europa by as much as 300 km (worst case),  of Callisto by
   as much as 3 km.
 */

/* Formulae taken from Jean Meeus' _Astronomical Algorithms_.  WARNING:
   the coordinates returned in the 'jsats' array are ecliptic Cartesian
   coordinates of _date_,  not J2000 or B1950!  Units are Jovian radii.
   Input time is in TD.                            */

static int calc_jsat_loc(const double jd, double *jsats,
                         const int sats_wanted, const long precision)
{
   const double t = jd - 2443000.5;          /* 1976 aug 10, 0:00 TD */
               /* calc precession since B1950 epoch */
   const double precess_time = (jd - 2433282.423) / 36525.;
   const double precession =
              LINEAR_FUNC(1.3966626, .0003088, precess_time) * precess_time;
   const double dt = (jd - J2000) / 36525.;
                  /* mean longitudes of satellites, p 289: */
   const double l1 = LINEAR_FUNC(106.07719, 203.488955790, t);
   const double l2 = LINEAR_FUNC(175.73161, 101.374724735, t);
   const double l3 = LINEAR_FUNC(120.55883,  50.317609209, t);
   const double l4 = LINEAR_FUNC( 84.44459,  21.571071177, t);

                  /* longitudes of perijoves: */
   const double pi1 = LINEAR_FUNC( 97.0881, 0.16138586, t);
   const double pi2 = LINEAR_FUNC(154.8663, 0.04726307, t);
   const double pi3 = LINEAR_FUNC(188.1840, 0.00712734, t);
   const double pi4 = LINEAR_FUNC(335.2868, 0.00184000, t);

                  /* longitudes of ascending nodes */
                  /* on Jupiter's equatorial plane: */
   const double ome1 = LINEAR_FUNC(312.3346, -0.13279386, t);
   const double ome2 = LINEAR_FUNC(100.4411, -0.03263064, t);
   const double ome3 = LINEAR_FUNC(119.1942, -0.00717703, t);
   const double ome4 = LINEAR_FUNC(322.6168, -0.00175934, t);

         /* Longitude of Jupiter's ascending node;  p. 213 */
         /* (table 31A)                                    */
   const double asc_node = CUBIC_FUNC(100.464407, 1.0209774, .00040315, 4.04e-7, dt);

         /* Inclination of Jupiter's orbit; same source */
   const double incl_orbit = CUBIC_FUNC(1.303267, -.0054965, 4.66e-6, -2.e-9, dt);

         /* gam = Gamma, principal inequality in the longitude of Jupiter */
   const double temp1 = LINEAR_FUNC( 163.679,  0.0010512, t);
   const double temp2 = LINEAR_FUNC(  34.486, -0.0161731, t);
   const double gam = 0.33033 * DEG2RAD * sin( temp1) + 0.03439 * DEG2RAD * sin( temp2);

         /* "There is a small libration, with a period of 2071 days,  in */
         /* the longitudes of the three inner satellites: when satellite */
         /* II decelerates,  I and III accelerate.  To take this into    */
         /* account,  we need the phase of free libration..."            */
   const double libration = LINEAR_FUNC(199.6766, 0.17379190, t);

      /* Longitude of the node of the equator of Jupiter on the ecliptic: */
   const double psi = LINEAR_FUNC(316.5182, -2.08e-6, t);
      /* Mean anomalies of Jupiter and Saturn: */
   const double g = LINEAR_FUNC( 30.23756, 0.0830925701, t) + gam;
   const double g_prime = LINEAR_FUNC( 31.97853, 0.0334597339, t);
   const double twice_per_plus_g = 2. * g + 2. * PER;

              /* Inclination of Jupiter's axis to its orbital plane: */
   const double incl = LINEAR_FUNC(3.120262, .0006, (jd - J1900) / 36525.);
   double lon[5], tan_lat[5], rad[5];
   double loc[18];
   int i;

   for( i = 1; i < 5; i++) {
      lon[i] = tan_lat[i] = rad[i] = 0.;
   }

   if( sats_wanted & 1)       /* Io */
   {                          /* NOTE: smaller terms omitted here! */
      const double del1 =
               47259. * COEFF2RAD * sin(2. * (l1 - l2))
               -3478. * COEFF2RAD * sin(pi3 - pi4)
               +1081. * COEFF2RAD * sin(l2 - 2. * l3 + pi3)
               + 738. * COEFF2RAD * sin(libration)
               + 713. * COEFF2RAD * sin(l2 - l3 - l3 + pi2)
               - 674. * COEFF2RAD * sin(pi1 + pi3 - twice_per_plus_g)
               + 666. * COEFF2RAD * sin(l2 - 2. * l3 + pi4)
               + 445. * COEFF2RAD * sin(l1 - pi3)
               - 354. * COEFF2RAD * sin(l1 - l2)
               - 317. * COEFF2RAD * sin(2. * psi - 2. * PER)
               + 265. * COEFF2RAD * sin(l1 - pi4)
               - 186. * COEFF2RAD * sin(g)
               + 162. * COEFF2RAD * sin(pi2 - pi3)
               + 158. * COEFF2RAD * sin(4. * (l1 - l2))
               - 155. * COEFF2RAD * sin(l1 - l3);

      lon[1] = l1 + del1;
      tan_lat[1] = 6393.e-7 * sin(lon[1] - ome1)
             + 1825.e-7 * sin(lon[1] - ome2)
             +  329.e-7 * sin(lon[1] - ome3)
             +  311.e-7 * sin(lon[1] - psi)
             +   93.e-7 * sin(lon[1] - ome4);
      rad[1] = -41339.e-7 * cos(2. * (l1 - l2))
               -  387.e-7 * cos(l1 - pi1)
               -  214.e-7 * cos(l1 - pi4)
               +  170.e-7 * cos(l1 - l2)
               -  131.e-7 * cos(4. * (l1 - l2))
               +  106.e-7 * cos(l1 - l3);
      }

   if( sats_wanted & 2)       /* europa */
   {                          /* NOTE: smaller terms omitted here! */
      const double del2 =
               106476. * COEFF2RAD * sin(2. * (l2 - l3))
                +4256. * COEFF2RAD * sin(l1 - l2 - l2 + pi3)
                +3581. * COEFF2RAD * sin(l2 - pi3)
                +2395. * COEFF2RAD * sin(l1 - l2 - l2 + pi4)
                +1984. * COEFF2RAD * sin(l2 - pi4)
                -1778. * COEFF2RAD * sin(libration)
                +1654. * COEFF2RAD * sin(l2 - pi2)
                +1334. * COEFF2RAD * sin(l2 - l3 - l3 + pi2)
                +1294. * COEFF2RAD * sin(pi3 - pi4)    /* KA fix */
                -1142. * COEFF2RAD * sin(l2 - l3)
                -1057. * COEFF2RAD * sin(g)
                - 775. * COEFF2RAD * sin(2. * ( psi - PER))
                + 524. * COEFF2RAD * sin(2. * (l1 - l2))
                - 460. * COEFF2RAD * sin(l1 - l3)
                + 316. * COEFF2RAD * sin(psi + ome3 - twice_per_plus_g)
                - 203. * COEFF2RAD * sin(pi1 + pi3 - twice_per_plus_g)
                + 146. * COEFF2RAD * sin(psi - ome3)
                - 145. * COEFF2RAD * sin(g + g)
                + 125. * COEFF2RAD * sin(psi - ome4)
                - 115. * COEFF2RAD * sin(l1 - 2. * l3 + pi3)
                -  94. * COEFF2RAD * sin(2. * (l2 - ome2));

      lon[2] = l2 + del2;
      tan_lat[2] = 81004.e-7 * sin(lon[2] - ome2)
               +4512.e-7 * sin(lon[2] - ome3)
               -3284.e-7 * sin(lon[2] - psi)
               +1160.e-7 * sin(lon[2] - ome4)
               + 272.e-7 * sin(l1 - 2. * l3 + 1.0146 * del2 + ome2)
               - 144.e-7 * sin(lon[2] - ome1)
               + 143.e-7 * sin(lon[2] + psi - twice_per_plus_g);
      rad[2] = 93848.e-7 * cos(l1 - l2)
               -3116.e-7 * cos(l2 - pi3)
               -1744.e-7 * cos(l2 - pi4)
               -1442.e-7 * cos(l2 - pi2)
               + 553.e-7 * cos(l2 - l3)
               + 523.e-7 * cos(l1 - l3)
               - 290.e-7 * cos(2. * (l1 - l2))
               + 164.e-7 * cos(2. * (l2 - ome2))
               + 107.e-7 * cos(l1 - 2. * l3 + pi3)
               - 102.e-7 * cos(l2 - pi1)
               -  91.e-7 * cos(2. * (l1 - l3));
   }

   if( sats_wanted & 4)       /* ganymede */
   {                          /* NOTE: smaller terms omitted here! */
      const double del3 =
               16490. * COEFF2RAD * sin(l3 - pi3)
               +9081. * COEFF2RAD * sin(l3 - pi4)
               -6907. * COEFF2RAD * sin(l2 - l3)
               +3784. * COEFF2RAD * sin(pi3 - pi4)
               +1846. * COEFF2RAD * sin(2. * (l3 - l4))
               -1340. * COEFF2RAD * sin(g)
               -1014. * COEFF2RAD * sin(2. * ( psi - PER))
               + 704. * COEFF2RAD * sin(l2 - l3 - l3 + pi3)
               - 620. * COEFF2RAD * sin(l2 - l3 - l3 + pi2)
               - 541. * COEFF2RAD * sin(l3 - l4)
               + 381. * COEFF2RAD * sin(l2 - l3 - l3 + pi4)
               + 235. * COEFF2RAD * sin(psi - ome3)
               + 198. * COEFF2RAD * sin(psi - ome4)
               + 176. * COEFF2RAD * sin(libration)
               + 130. * COEFF2RAD * sin(3. * (l3 - l4))
               + 125. * COEFF2RAD * sin(l1 - l3)
               - 119. * COEFF2RAD * sin(5. * g_prime - 2. * g + 52.225 * DEG2RAD)
               + 109. * COEFF2RAD * sin(l1 - l2)
               - 100. * COEFF2RAD * sin(3. * l3 - 7. * l4 + 4. * pi4)
               +  91. * COEFF2RAD * sin(ome3 - ome4)
               +  80. * COEFF2RAD * sin(3. * l3 - 7. * l4 + pi3 + 3. * pi4)
               -  75. * COEFF2RAD * sin(2. * l2 - 3. * l3 + pi3)
               +  72. * COEFF2RAD * sin(pi1 + pi3 - twice_per_plus_g)
               +  69. * COEFF2RAD * sin(pi4 - PER)
               -  58. * COEFF2RAD * sin(2. * l3 - 3. * l4 + pi4)
               -  57. * COEFF2RAD * sin(l3 - 2. * l4 + pi4)
               +  56. * COEFF2RAD * sin(l3 + pi3 - twice_per_plus_g)
               -  52. * COEFF2RAD * sin(l2 - 2. * l3 + pi1)
               -  50. * COEFF2RAD * sin(pi2 - pi3);

      lon[3] = l3 + del3;
      tan_lat[3] = 32402.e-7 * sin(lon[3] - ome3)
              -16911.e-7 * sin(lon[3] - psi)
               +6847.e-7 * sin(lon[3] - ome4)
               -2797.e-7 * sin(lon[3] - ome2)
               + 321.e-7 * sin(lon[3] + psi - twice_per_plus_g)
               +  51.e-7 * sin(lon[3] - psi + g)
               -  45.e-7 * sin(lon[3] - psi - g)
               -  45.e-7 * sin(lon[3] - psi - 2. * PER);
      rad[3] = -14388.e-7 * cos(l3 - pi3)
                -7919.e-7 * cos(l3 - pi4)
                +6342.e-7 * cos(l2 - l3)
                -1761.e-7 * cos(2. * (l3 - l4))
                + 294.e-7 * cos(l3 - l4)
                - 156.e-7 * cos(3. * (l3 - l4))
                + 156.e-7 * cos(l1 - l3)
                - 153.e-7 * cos(l1 - l2)
                -  70.e-7 * cos(2. * l2 - 3. * l3 + pi3);
   }

   if( sats_wanted & 8)       /* callisto */
   {                          /* NOTE: smaller terms omitted here! */
      const double del4 =
               84287. * COEFF2RAD * sin(l4 - pi4)
              + 3431. * COEFF2RAD * sin(pi4 - pi3)
              - 3305. * COEFF2RAD * sin(2. * (psi - PER))
              - 3211. * COEFF2RAD * sin(g)
              - 1862. * COEFF2RAD * sin(l4 - pi3)
              + 1186. * COEFF2RAD * sin(psi - ome4)
              +  623. * COEFF2RAD * sin(l4 + pi4 - twice_per_plus_g)
              +  387. * COEFF2RAD * sin(2. * (l4 - pi4))
              -  284. * COEFF2RAD * sin(5. * g_prime - 2. * g + 52.225 * DEG2RAD)
              -  234. * COEFF2RAD * sin(2. * (psi - pi4))
              -  223. * COEFF2RAD * sin(l3 - l4)         /* KA fix */
              -  208. * COEFF2RAD * sin(l4 - PER)
              +  178. * COEFF2RAD * sin(psi + ome4 - 2. * pi4)
              +  134. * COEFF2RAD * sin(pi4 - PER)
              +  125. * COEFF2RAD * sin(2. * l4 - twice_per_plus_g)
              -  117. * COEFF2RAD * sin(2. * g)
              -  112. * COEFF2RAD * sin(2. * (l3 - l4));

      lon[4] = l4 + del4;
      tan_lat[4] = - 76579.e-7 * sin(lon[4] - psi)
               + 44134.e-7 * sin(lon[4] - ome4)
               -  5112.e-7 * sin(lon[4] - ome3)
               +   773.e-7 * sin(lon[4] + psi - twice_per_plus_g)
               +   104.e-7 * sin(lon[4] - psi + g)
               -   102.e-7 * sin(lon[4] - psi - g)
               +    88.e-7 * sin(lon[4] + psi - twice_per_plus_g - g)
               -    38.e-7 * sin(lon[4] + psi - twice_per_plus_g + g);
      rad[4] = -73546.e-7 * cos(l4 - pi4)
                +1621.e-7 * cos(l4 - pi3)
                + 974.e-7 * cos(l3 - l4)
                - 543.e-7 * cos(l4 + pi4 - twice_per_plus_g)
                - 271.e-7 * cos(2. * (l4 - pi4))
                + 182.e-7 * cos(l4 - PER)
                + 177.e-7 * cos(2. * (l3 - l4))
                - 167.e-7 * cos(2. * l4 - psi - ome4)
                + 167.e-7 * cos(psi - ome4)
                - 155.e-7 * cos(2. * l4 - twice_per_plus_g)
                + 142.e-7 * cos(2. * (l4 - psi))
                + 105.e-7 * cos(l1 - l4)
                +  92.e-7 * cos(l2 - l4)
                -  89.e-7 * cos(l4 - PER - g)
                -  62.e-7 * cos(l4 + pi4 - twice_per_plus_g - g)
                +  48.e-7 * cos(2. * (l4 - ome4));
   }

   for( i = 0; i < 15; i++) {
      loc[i] = 0.;
   }

   for( i = 1; i < 6; i++)
   {
      if( sats_wanted & (1 << (i - 1)))
      {
         double *tptr = (double *)loc + (i - 1) * 3;

                                    /* calc coords by Jupiter's equator */
         if( i != 5)
         {
            static const double r0[4] = { 5.90569, 9.39657, 14.98832, 26.36273 };
            const double csc_lat = sqrt(1. + tan_lat[i] * tan_lat[i]);
            const double r = r0[i - 1] * (1. + rad[i]);

            tptr[0] = r * cos(lon[i] - psi) / csc_lat;
            tptr[1] = r * sin(lon[i] - psi) / csc_lat;
            tptr[2] = r * tan_lat[i] / csc_lat;
         }
         else
         {
            tptr[2] = 1.;     /* fictitious fifth satellite */
         }

                            /* rotate to plane of Jup's orbit: */
         rotate_vector(incl, tptr + 1, tptr + 2);

                            /* rotate to Jup's ascending node: */
         rotate_vector(psi + precession - asc_node, tptr, tptr + 1);

                            /* rotate to the ecliptic */
         rotate_vector(incl_orbit, tptr + 1, tptr + 2);

                            /* rotate to vernal equinox.  This results */
                            /* in ecliptic coords of date.  In Meeus,  */
                            /* topo[0...2] will be A4, B4, C4.         */
         rotate_vector(asc_node, tptr, tptr + 1);
                            /* Meeus does further rotations to get into */
                            /* a system in which the z-axis points from */
                            /* earth to Jupiter and y points along the  */
                            /* rotation axis of Jupiter.  We don't need */
                            /* any of that here.                        */
      }
   }
   memcpy(jsats, loc, 12 * sizeof( double));
   if(sats_wanted & 16) {    /* imaginary sat wanted */
      memcpy(jsats + 12, loc + 12, 3 * sizeof( double));
   }
   return(sats_wanted);
}

LPoint3d
lieske_e5_sat_pos(double jd, int sat)
{
  double loc[15];
  calc_jsat_loc(jd, loc, 1 << sat, 0);
  int i = sat * 3;
  return LPoint3d(loc[i + 0] * JRADIUS_IN_KM,
                  loc[i + 1] * JRADIUS_IN_KM,
                  loc[i + 2] * JRADIUS_IN_KM);
}
