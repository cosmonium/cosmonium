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

#include "gust86.h"

/* gust86.cpp: functions for Uranian satellite coords

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

/*
** gust86.cpp
** Implementation of the Lascar and Jacobson theory of the
** motion of the satellites of Uranus.  Written by Chris Marriott for
** SkyMap,  with some modifications by me (Bill J. Gray).
** Based on :
**
**  Laskar J., Jacobson, R.: 1987, GUST86 - An analytical ephemeris of the
**  Uranian satellites, Astron. Astrophys. 188, 212-224
** http://articles.adsabs.harvard.edu/cgi-bin/nph-journal_query?volume=188&plate_select=NO&page=212&plate=&cover=&journal=A%2BA..
**
** Created:   17-JUL-98
**
** $History: gust86.cpp $
**
   1 Feb 2012:  BJG:  Revised code to avoid errors on stricter compilers
such as OpenWATCOM.

   5 Nov 2008:  BJG:  Revised code to be more C-like and less C++-like,
did general cleanup & simplifying.  Now,  you can just get positions
and velocities with one relatively simple function.

** 10 Jan 2003: Bill J Gray:  changed the output from B1950 to J2000,
** by replacing the Uranicentric-to-B1950 matrix in "Position( )" with
** an Uranicentric-to-J2000 one.  (The original code is still available
** with #define ORIGINAL_B1950.)
**
**    The individual "per-satellite" functions contained a great deal
** of code identical except for coefficient values; I put that code into
** sum_uranian_series() with the coefficients passed in as arrays.
**    Most (though not all!) comments are now in English instead of French.
**
** *****************  Version 1  *****************
** User: Chris        Date: 2/10/98    Time: 6:54
** Created in $/SkyMap 4.0
** Moved from solar system DLL into main project.
**
** *****************  Version 2  *****************
** User: Chris        Date: 18/07/98   Time: 4:49p
** Updated in $/SkyMap 4.0/SolarSys
** Initial working version.
**
** *****************  Version 1  *****************
** User: Chris        Date: 17/07/98   Time: 11:59a
** Created in $/SkyMap 4.0/SolarSys
** Initial version.
*/

#include <math.h>
#include <assert.h>
#include "lunar.h"

#define GUST86_ARIEL          0
#define GUST86_UMBRIEL        1
#define GUST86_TITANIA        2
#define GUST86_OBERON         3
#define GUST86_MIRANDA        4

static double an[5], ae[5], ai[5];         // satellite position data

//   OrbitalPosition
//   Compute basic orbital position data for the satellites.

static void
gust86_mean_parameters(const double jde)
{
   static double curr_jde_set = -1.;

   if (jde != curr_jde_set)
   {
      const double t0 = 2444239.5;   // origin date for the theory: 1980 Jan 1
      const double days_since_1980 = jde - t0;             // time from origin
      const double days_per_year = 365.25;                 // days in a year
      const double years_since_1980 = days_since_1980 / days_per_year;
      int i;                           // loop counter

      static const double fqn[5] =    /* mean motion at epoch in radians/day */
      {
         4445190.550e-06, 2492952.519e-06, 1516148.111e-06,
          721718.509e-06, 466692.120e-06
      };

      static const double fqe[5] =     /* in degrees/year */
      {
         20.082, 6.217, 2.865, 2.078, 0.386
      };

      static const double fqi[5] =     /* in degrees/year */
      {
         -20.309, -6.288, -2.836, -1.843, -0.259
      };

      static const double phn[5] =     /* mean longitude at epoch in radians */
      {
         -238051.e-06, 3098046.e-06, 2285402.e-06,
           856359.e-06, -915592.e-06
      };

      static const double phe[5] =   /* in radians */
      {
         0.611392, 2.408974, 2.067774, 0.735131, 0.426767
      };

      static const double phi[5] =   /* in radians */
      {
         5.702313, 0.395757, 0.589326, 1.746237, 4.206896
      };

      // Compute the orbital data.

      for (i = 0; i < 5; i++)
      {
         an[i] = fqn[i] * days_since_1980 + phn[i];
         ae[i] = fqe[i] * DEG2RAD * years_since_1980 + phe[i];
         ai[i] = fqi[i] * DEG2RAD * years_since_1980 + phi[i];
      }
   }
}

static void
sum_uranian_series(double *elems,
      const double *ae_series, const double *aet,
      const double *ai_series, const double *ait,
      const double *amplitudes, const double *phases, int n_extra_terms)
{
   int i;

   for (i = 2; i < 6; i++) {
      elems[i] = 0;
   }
   for (i = 5; i; i--)
   {
      elems[2] += *ae_series   * cos(*aet  );
      elems[3] += *ae_series++ * sin(*aet++);
      elems[4] += *ai_series   * cos(*ait  );
      elems[5] += *ai_series++ * sin(*ait++);
   }
   while (n_extra_terms--)
   {
      elems[2] += *amplitudes   * cos(*phases);
      elems[3] += *amplitudes++ * sin(*phases++);
   }
}

//   miranda_elems
//   Compute the orbital elements of Miranda.

static void
miranda_elems(const double t, double *elems)
{
/* --- Z = K + IH  ---- */
   static const double ae_series[5] = { 1312.38e-6, 71.81e-6, 69.77e-6,
            6.75e-6, 6.27e-6 };
   static const double amplitudes[3] = {
               -123.31e-6, 39.52e-6, 194.10e-6 };
   double phases[3];
/* --- ZETA = Q + IP --- */
   static const double ai_series[5] = { 37871.71e-06, +27.01e-06, +30.76e-06,
                  +12.18e-06, +5.37e-06 };
/* --- RN => mean motion (radians/day) ---- */
   elems[0] = 4443522.67e-06
              -34.92e-06*cos(an[0]-3.e0*an[1]+2.e0*an[2])
               +8.47e-06*cos(2.*an[0]-6.*an[1]+4.*an[2])
               +1.31e-06*cos(3.*an[0]-9.*an[1]+6.*an[2])
              -52.28e-06*cos(an[0]-an[1])
             -136.65e-06*cos(2.*an[0]-2.*an[1]);
/* --- RL => mean longitude (radians) ---- */
   elems[1] =  -238051.58e-06
          +4445190.55e-06*t
            +25472.17e-06*sin(an[0]-3.*an[1]+2.*an[2])
             -3088.31e-06*sin(2.*an[0]-6.*an[1]+4.*an[2])
              -318.10e-06*sin(3.*an[0]-9.*an[1]+6.*an[2])
               -37.49e-06*sin(4.*an[0]-12.*an[1]+8.*an[2])
               -57.85e-06*sin(an[0]-an[1])
               -62.32e-06*sin(2.*an[0]-2.*an[1])
               -27.95e-06*sin(3.*an[0]-3.*an[1]);
   phases[0] = -an[0] + 2.*an[1];
   phases[1] = -2. * an[0] + 3.*an[1];
   phases[2] = an[0];

   sum_uranian_series(elems, ae_series, ae, ai_series, ai,
               amplitudes, phases, 3);
}


//   ariel_elems
//   Compute the orbital elements of Ariel.

static void
ariel_elems(const double t, double *elems)
{
/* --- Z = K + IH --- */
   static const double ae_series[5] = { -3.35e-6, 1187.63e-6, 861.59e-6,
         71.50e-6, 55.59e-6 };
   static const double ai_series[5] = { -121.75e-6, 358.25e-06, 290.08e-06,
                   97.78e-06, 33.97e-06 };
   static const double amplitudes[4] = {
            -84.60e-06, +91.81e-06, +20.03e-06, +89.77e-06 };
   double phases[4];

/* --- RN => mean motion (radians/day) --- */
   elems[0] = 2492542.57e-06
                +2.55e-06*cos(an[0]-3.*an[1]+2.*an[2])
               -42.16e-06*cos(an[1]-an[2])
              -102.56e-06*cos(2.*an[1]-2.*an[2]);
/* --- RL => mean longitude (radians) --- */
   elems[1] =   3098046.41e-06
            +2492952.52e-06*t
               -1860.50e-06*sin(an[0]-3.*an[1]+2.*an[2])
                +219.99e-06*sin(2.*an[0]-6.*an[1]+4.*an[2])
                 +23.10e-06*sin(3.*an[0]-9.*an[1]+6.*an[2])
                  +4.30e-06*sin(4.*an[0]-12.*an[1]+8.*an[2])
                 -90.11e-06*sin(an[1]-an[2])
                 -91.07e-06*sin(2.*an[1]-2.*an[2])
                 -42.75e-06*sin(3.*an[1]-3.*an[2])
                 -16.49e-06*sin(2.*an[1]-2.*an[3]);
   phases[0] =  2. * an[2] - an[1];
   phases[1] =  3. * an[2] - 2. * an[1];
   phases[2] =  2. * an[3] - an[1];
   phases[3] =  an[1];

   sum_uranian_series(elems, ae_series, ae, ai_series, ai,
               amplitudes, phases, 4);
/*
*---- ZETA = Q + IP ----------------------------------------------------
*/

}


//   umbriel_elems
//   Compute the orbital elements of Umbriel.

static void
umbriel_elems(const double t, double *elems)
{
/* --- Z = K + IH --- */
   static const double ae_series[5] = { -0.21e-6, -227.95e-6, 3904.69e-6,
          309.17e-6, 221.92e-6 };
   static const double ai_series[5] = { -10.86e-6, -81.51e-06, 1113.36e-06,
                  350.14e-06, 106.50e-06 };
   static const double amplitudes[11] = {
               29.34e-6, 26.20e-6, 51.19e-6, -103.86e-6, -27.16e-6,
               -16.22e-6, 549.23e-6, 34.70e-6, 12.81e-6, 21.81e-6,
               46.25e-6 };
   double phases[11];

/* --- RN => mean motion (radians/day) --- */
   elems[0] =  1515954.90e-06
                 +9.74e-06*cos(an[2]-2.*an[3]+ae[2])
               -106.00e-06*cos(an[1]-an[2])
                +54.16e-06*cos(2.*an[1]-2.*an[2])
                -23.59e-06*cos(an[2]-an[3])
                -70.70e-06*cos(2.*an[2]-2.*an[3])
                -36.28e-06*cos(3.*an[2]-3.*an[3]);
/* --- RL => mean longitude (radians) --- */
   elems[1] =  2285401.69e-06
            +1516148.11e-06*t
                +660.57e-06*sin(an[0]-3.*an[1]+2.*an[2])
                 -76.51e-06*sin(2.*an[0]-6.*an[1]+4.*an[2])
                  -8.96e-06*sin(3.*an[0]-9.*an[1]+6.*an[2])
                  -2.53e-06*sin(4.*an[0]-12.*an[1]+8.*an[2])
                 -52.91e-06*sin(an[2]-4.*an[3]+3.*an[4])
                  -7.34e-06*sin(an[2]-2.*an[3]+ae[4])
                  -1.83e-06*sin(an[2]-2.*an[3]+ae[3])
                +147.91e-06*sin(an[2]-2.*an[3]+ae[2]);

   elems[1] +=       -7.77e-06*sin(an[2]-2.*an[3]+ae[1])
                 +97.76e-06*sin(an[1]-an[2])
                 +73.13e-06*sin(2.*an[1]-2.*an[2])
                 +34.71e-06*sin(3.*an[1]-3.*an[2])
                 +18.89e-06*sin(4.*an[1]-4.*an[2])
                 -67.89e-06*sin(an[2]-an[3])
                 -82.86e-06*sin(2.*an[2]-2.*an[3]);

   elems[1] +=      -33.81e-06*sin(3.*an[2]-3.*an[3])
                 -15.79e-06*sin(4.*an[2]-4.*an[3])
                 -10.21e-06*sin(an[2]-an[4])
                 -17.08e-06*sin(2.*an[2]-2.*an[4]);

   phases[0]  = an[1];
   phases[1]  = an[2];
   phases[2]  = -an[1]+2.*an[2];
   phases[3]  = -2.*an[1]+3.*an[2];
   phases[4]  = -3.*an[1]+4.*an[2];
   phases[5]  =  an[3];
   phases[6]  = -an[2]+2.*an[3];
   phases[7]  = -2.*an[2]+3.*an[3];
   phases[8]  = -3.*an[2]+4.*an[3];
   phases[9]  = -an[2]+2.*an[4];
   phases[10] = an[2];

   sum_uranian_series(elems, ae_series, ae, ai_series, ai,
               amplitudes, phases, 11);

/*
*---- ZETA = Q + IP ----------------------------------------------------
*/
}


//   titania_elems
//   Compute the orbital elements of Titania.

static void
titania_elems(const double t, double *elems)
{
   static const double ae_series[5] = { -0.02e-6, -1.29e-6, -324.51e-6,
                  932.81e-6, 1120.89e-6 };
   static const double ai_series[5] = { -1.43e-6, -1.06e-06, -140.13e-06,
                  685.72e-06, 378.32e-06 };
   static const double amplitudes[13] = {
                33.86e-6, 17.46e-6, 16.58e-6, 28.89e-6, -35.86e-6,
                -17.86e-6, -32.10e-6, -177.83e-6, 793.43e-6, 99.48e-6,
                44.83e-6, 25.13e-6, 15.43e-6 };
   double phases[13];

/* --- RN => mean motion (radians/day) --- */
   elems[0] = 721663.16e-06
                -2.64e-06*cos(an[2]-2.*an[3]+ae[2])
                -2.16e-06*cos(2.*an[3]-3.*an[4]+ae[4])
                +6.45e-06*cos(2.*an[3]-3.*an[4]+ae[3])
                -1.11e-06*cos(2.*an[3]-3.*an[4]+ae[2]);

   elems[0] +=   -62.23e-06*cos(an[1]-an[3])
               -56.13e-06*cos(an[2]-an[3])
               -39.94e-06*cos(an[3]-an[4])
               -91.85e-06*cos(2.*an[3]-2.*an[4])
               -58.31e-06*cos(3.*an[3]-3.*an[4])
               -38.60e-06*cos(4.*an[3]-4.*an[4])
               -26.18e-06*cos(5.*an[3]-5.*an[4])
               -18.06e-06*cos(6.*an[3]-6.*an[4]);
/* --- RL => mean longitude (radians) --- */
   elems[1] =  856358.79e-06
            +721718.51e-06*t
                +20.61e-06*sin(an[2]-4.*an[3]+3.*an[4])
                 -2.07e-06*sin(an[2]-2.*an[3]+ae[4])
                 -2.88e-06*sin(an[2]-2.*an[3]+ae[3])
                -40.79e-06*sin(an[2]-2.*an[3]+ae[2])
                 +2.11e-06*sin(an[2]-2.*an[3]+ae[1])
                -51.83e-06*sin(2.*an[3]-3.*an[4]+ae[4])
               +159.87e-06*sin(2.*an[3]-3.*an[4]+ae[3]);

   elems[1]  +=    -35.05e-06*sin(2.*an[3]-3.*an[4]+ae[2])
                 -1.56e-06*sin(3.*an[3]-4.*an[4]+ae[4])
                +40.54e-06*sin(an[1]-an[3])
                +46.17e-06*sin(an[2]-an[3])
               -317.76e-06*sin(an[3]-an[4])
               -305.59e-06*sin(2.*an[3]-2.*an[4])
               -148.36e-06*sin(3.*an[3]-3.*an[4])
                -82.92e-06*sin(4.*an[3]-4.*an[4]);

   elems[1]  +=    -49.98e-06*sin(5.*an[3]-5.*an[4])
                -31.56e-06*sin(6.*an[3]-6.*an[4])
                -20.56e-06*sin(7.*an[3]-7.*an[4])
                -13.69e-06*sin(8.*an[3]-8.*an[4]);
   phases[0] = an[1];
   phases[1] = an[3];
   phases[2] = -an[1]+2.*an[3];
   phases[3] = an[2];
   phases[4] = -an[2]+2.*an[3];
   phases[5] = an[3];
   phases[6] = an[4];
   phases[7] = -an[3]+2.*an[4];
   phases[8] = -2.*an[3]+3.*an[4];
   phases[9] = -3.*an[3]+4.*an[4];
   phases[10] = -4.*an[3]+5.*an[4];
   phases[11] = -5.*an[3]+6.*an[4];
   phases[12] = -6.*an[3]+7.*an[4];

   sum_uranian_series(elems, ae_series, ae, ai_series, ai,
               amplitudes, phases, 13);
/*
*---- ZETA= Q + IP ----------------------------------------------------
*/
}

//   oberon_elems
//   Compute the orbital elements of Oberon.

static void
oberon_elems( const double t, double *elems)
{
   static const double ae_series[5] = { 0.00e-6, -0.35e-6, 74.53e-6,
           -758.68e-6, 1397.34e-6 };
   static const double ai_series[5] = { -0.44e-6, -0.31e-06, 36.89e-06,
                 -596.33e-06, 451.69e-06 };
   static const double amplitudes[12] = {
            39.00e-6, 17.66e-6, 32.42e-6, 79.75e-6, 75.66e-6, 134.04e-6,
            -987.26e-6, -126.09e-6, -57.42e-6, -32.41e-6, -19.99e-6, -12.94e-6 };
   double phases[12];

/* --- RN => mean motion (radians/day) --- */
   elems[0] = 466580.54e-06
                +2.08e-06*cos(2.*an[3]-3.*an[4]+ae[4])
                -6.22e-06*cos(2.*an[3]-3.*an[4]+ae[3])
                +1.07e-06*cos(2.*an[3]-3.*an[4]+ae[2])
               -43.10e-06*cos(an[1]-an[4]);

   elems[0] +=    -38.94e-06*cos(an[2]-an[4])
               -80.11e-06*cos(an[3]-an[4])
               +59.06e-06*cos(2.*an[3]-2.*an[4])
               +37.49e-06*cos(3.*an[3]-3.*an[4])
               +24.82e-06*cos(4.*an[3]-4.*an[4])
               +16.84e-06*cos(5.*an[3]-5.*an[4]);

   elems[1] =  -915591.80e-06
             +466692.12e-06*t
                  -7.82e-06*sin(an[2]-4.*an[3]+3.*an[4])
                 +51.29e-06*sin(2.*an[3]-3.*an[4]+ae[4])
                -158.24e-06*sin(2.*an[3]-3.*an[4]+ae[3])
                 +34.51e-06*sin(2.*an[3]-3.*an[4]+ae[2])
                 +47.51e-06*sin(an[1]-an[4])
                 +38.96e-06*sin(an[2]-an[4])
                +359.73e-06*sin(an[3]-an[4]);

   elems[1] +=      282.78e-06*sin(2.*an[3]-2.*an[4])
                +138.60e-06*sin(3.*an[3]-3.*an[4])
                 +78.03e-06*sin(4.*an[3]-4.*an[4])
                 +47.29e-06*sin(5.*an[3]-5.*an[4])
                 +30.00e-06*sin(6.*an[3]-6.*an[4])
                 +19.62e-06*sin(7.*an[3]-7.*an[4])
                 +13.11e-06*sin(8.*an[3]-8.*an[4]);

    phases[0] = an[1];
    phases[1] = -an[1]+2.*an[4];
    phases[2] = an[2];
    phases[3] = an[3];
    phases[4] = an[4];
    phases[5] = -an[3]+2.*an[4];
    phases[6] = -2.*an[3]+3.*an[4];
    phases[7] = -3.*an[3]+4.*an[4];
    phases[8] = -4.*an[3]+5.*an[4];
    phases[9] = -5.*an[3]+6.*an[4];
    phases[10] = -6.*an[3]+7.*an[4];
    phases[11] = -7.*an[3]+8.*an[4];

   sum_uranian_series( elems, ae_series, ae, ai_series, ai,
               amplitudes, phases, 12);

/*
*---- ZETA = Q + IP ---------------------------------------------------
*/
}

//   keplkh
//   Solve Kepler's equation.

static double
keplkh(const double rl, const double rk, const double rh)
{
/*
      SUBROUTINE KEPLKH (RL,RK,RH,F,IT,IPRT)
*
*---- KEPLKH  1.0  12 DECEMBRE 1985 J. LASKAR --------------------------
*
*     RESOLUTION DE L'EQUATION DE KEPLER EN VARIABLES LONGITUDES, K, H
*
*-----------------------------------------------------------------------
*
*/
   const double eps = 1.0e-16;
   double f;
   double f0, e0;
   const int itmax = 20;
   int it;

   if (rl==0.0)
      return( 0.);

   f0 = rl;
   e0 = fabs(rl);

   for (it=0; it<itmax; it++)
   {
      int k = 0;
      const double sf = sin(f0);
      const double cf = cos(f0);
      double e;
      const double ff0 = f0 - rk*sf + rh*cf - rl;
      const double fpf0 = 1.0 - rk*cf - rh*sf;
      double sdir = ff0/fpf0;
      double sdir_over_2_to_the_kth = sdir;

      do
      {
         f = f0 - sdir_over_2_to_the_kth;
         e = fabs(f - f0);
         if (e>e0)
         {
            k++;
            sdir_over_2_to_the_kth *= .5;
         }
      } while(e > e0);
      if (k==0 && e<=eps && ff0<=eps)
      {
         it = itmax;       /* time to break out of loop */
      }
      else
      {
         f0 = f;
         e0 = e;
      }
   }
   return (f);
}


//   ellipx
//   Compute rectangular coordinates from a set of orbital elements.

static void
ellipx(const double ell[6], const double rmu, double xyz[6])
{
/*
   SUBROUTINE ELLIPX (ELL,RMU,XYZ,DXYZ,IDER,IPRT)
*
*---- ELLIPX  1.1  18 March 1986  J. LASKAR -----------------------------
*
*     Calculate Cartesian coordinates (positions & velocities) and their
*     partial derivatives with respect to orbital elements,  given the
*     orbital elements as input.
*
*     ELL(6)     : Orbital elements     A: Semimajor axis
*                                       L: Mean longitude
*                                       K: ecc*COS(LONG asc node+ ARG PERI)
*                                       H: ecc*SIN(LONG asc node+ ARG PERI)
*                                       Q: SIN(Incl/2)*COS(asc node)
*                                       P: SIN(Incl/2)*SIN(asc node)
*     RMU        : Constant of gravitation for the two-body problem
*                  RMU = G*M1*(1+M2/M1) M1 Central mass
*                                       M2 Satellite mass
*     XYZ(6)     : State vector;  0..2 = position,  3..5 = velocity
*                  (The following three items were in the original code,
*                  but have been removed:)
*     DXYZ(6,7)  : Partial derivatives of the state vector with respect to
*                       the six orbital elements...
*                  DXYZ(I,J)=DRON(XYZ(I))/DRON(ELL(J))
*                       ...and with respect to the total GM:
*                  DXYZ(I,7)=DRON(XYZ(I))/DRON(RMU)
*     IDER       : 0 Get the state vector only,  or...
*                  1 Get the partial derivatives also
*     IPRT       : Print out results (not used)
*
*     Subroutine used: KEPLKH
*/
   double rot[2][3];
   double tx1[2], tx1t[2];
   double ra, rl, rk, rh, rp, rq;
   double rn, phi, psi, rki;
   int i, j;
   double f, sf, cf;
   double rlmf, umrsa, asr, rna2sr;

/*
*---- ELEMENTS UTILES --------------------------------------------------
*/
   ra=ell[0];
    rl=ell[1];
    rk=ell[2];
    rh=ell[3];
    rq=ell[4];
    rp=ell[5];
    rn=sqrt(rmu/(ra*ra*ra));
    phi=sqrt( 1.0 - rk*rk - rh*rh );
    rki = sqrt( 1.0 - rq*rq - rp*rp );
   psi = 1.0/(1.0 + phi);

/*
*---- Rotational matrix: ----------------------------------------------
*/
    rot[0][0] = 1.0 - 2*rp*rp;
   rot[1][0] = 2*rp*rq;
   rot[0][1] = 2*rp*rq;
   rot[1][1] = 1.0 - 2*rq*rq;
   rot[0][2] = -2*rp*rki;
   rot[1][2] = 2*rq*rki;

/*
*---- CALCUL DE LA LONGITUDE EXCENTRIQUE F -----------------------------
*---- F = ANOMALIE EXCENTRIQUE E + LONGITUDE DU PERIAPSE OMEGAPI -------
*/
      f = keplkh( rl, rk, rh);

      sf    =sin(f);
      cf    =cos(f);
      rlmf  =-rk*sf+rh*cf;
      umrsa =rk*cf+rh*sf;
      asr   =1.0/(1.0-umrsa);
      rna2sr=rn*ra*asr;
/*
*---- CALCUL DE TX1 ET TX1T --------------------------------------------
   tx1 = (x, y) location of satellite in the plane of its own orbit,
   tx1t = (vx, vy) in similar plane,  z = vz = 0.
*/
      tx1[0] =ra*(cf-psi*rh*rlmf-rk);
      tx1[1] =ra*(sf+psi*rk*rlmf-rh);
      tx1t[0]=rna2sr*(-sf+psi*rh*umrsa);
      tx1t[1]=rna2sr*( cf-psi*rk*umrsa);
/*
*---- CALCUL DE XYZ ----------------------------------------------------
   Now rotate from the plane of the orbit to the plane of Uranus' equator.
*/
   for (i=0; i<3; i++)
   {
         xyz[i]  =0.0;
         xyz[i+3]=0.0;

       for (j=0; j<2; j++)
       {
            xyz[i] += rot[j][i]*tx1[j];
            xyz[i+3] += rot[j][i]*tx1t[j];
       }
   }
}


//   Position
//   Compute position and velocity components for a single satellite
//   at a specified time.

static void
gust86_posn(const double jde, const int isat, double *r)

// Input arguments:
//   jde      Julian date, TDT
//   isat   Satellite index
//
//   Output arguments
//   r      Data array [0..2] position, [3..5] velocity components.
//         These are equatorial rectangular coordinates in km and
//         km/sec respectively, referred to epoch J2000.0.

{
   static const double gms[5] =
   {                               // GM of each of the five satellites
      4.4, 86.1, 84.0, 230.0, 200.0    // in km^3/s^2
   };
   const double AU_in_km = 149597870.0;         // 1AU in km
               // NOTE:  modern value is 149597870.7,  700 m larger
   const double t0 = 2444239.5;     // origin date for the theory = 1980 Jan 1
   const double gmsu = 5794554.5;   // Total GM of Uranus plus satellites,
                                    // in km^3/s^2
   const double gmu = gmsu - (gms[0]+gms[1]+gms[2]+gms[3]+gms[4]);
               /* Above is GM of Uranus alone,  without the satellites */
               /* Satellite GMs sum to 604.5;  gmu = 5794950.5         */
   const double rmu = gmu + gms[isat];
               /* Above is GM of Uranus plus the satellite we want */
   const double seconds_per_day = 24. * 60. * 60.;
   const double seconds_per_day_squared = seconds_per_day * seconds_per_day;
   const double days_since_1980 = jde - t0;
   double el[6], xu[6];
   int i, j;

/*---- INITIALISATIONS --------------------------------------------------*/

/*---- Test parameters: ----------------------------------------------*/

   gust86_mean_parameters(jde);
   // The function to call depends on the satellite.

   switch (isat)
   {
   case GUST86_ARIEL:
      ariel_elems(days_since_1980, el);
      break;

   case GUST86_UMBRIEL:
      umbriel_elems(days_since_1980, el);
      break;

   case GUST86_TITANIA:
      titania_elems(days_since_1980, el);
      break;

   case GUST86_OBERON:
      oberon_elems(days_since_1980, el);
      break;

   case GUST86_MIRANDA:
      miranda_elems(days_since_1980, el);
      break;

   default:       /* should never happen */
      assert (1);
      return;
   }

         /* el[0] from the above actually gives the mean motion,  in radians
            per day.  Use Kepler's 3rd law to convert this to a semimajor
            axis in kilometers. */

   el[0] = pow( rmu*seconds_per_day_squared/(el[0] * el[0]), 1.0/3.0 );

/*---- Calculate Uranicentric XYZ coordinates (position & velocity) ----- */
   ellipx( el, rmu, xu );

   for( i=0; i<6; i++) {
      r[i] = 0.0;
   }

         /* Output is in the Uranicentric frame of reference.  Doing   */
         /* a matrix multiply by 'trans' converts to J2000.  See       */
         /* 'gust_ref.cpp' for details as to how this matrix was made. */
   for( i=0; i<3; i++)
   {
      for( j=0; j<3; j++)
      {
       const double trans[3][3] = {
                 {  0.9753206898, -0.2207422915,  0.0047321138},
                 {  0.0619432123,  0.2529905682, -0.9654837185},
                 {  0.2119259083,  0.9419493686,  0.2604204221} };
         r[i] += trans[j][i]*xu[j];
         r[i+3] += trans[j][i]*xu[j+3];
      }
   }
}

LPoint3d
gust86_sat_pos(double jd, int sat)
{
  double loc[6];
  gust86_posn(jd, sat, loc);
  return LPoint3d(loc[0], loc[1], loc[2]);
}
