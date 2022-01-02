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

#include "dourneau.h"

/* ssats.cpp: functions for Saturnian satellite coordinates

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

#include <math.h>
#include "lunar.h"
#include "kepler.h"
#include "precess.h"
#include "mathutils.h"

/*
All references are from G. Dourneau unless otherwise noted.

The Phoebe orbital elements are from the _Explanatory Supplement to
the Astronomical Almanac_,  and should not be trusted very much;  they
are horribly outdated,  and don't match reality very well at all.
They are not actually used in any of my code.

There are a few places to look for alternative algorithms/code for the
satellites of Saturn.  Peter Duffett-Smith's book "Practical Astronomy
with your Calculator" provides a simpler theory,  with mostly circular
orbits,  and Dan Bruton has implemented this in BASIC code in his
SATSAT2 program.  At the other extreme,  the Bureau des Longitudes
(http://www.bdl.fr) provides Fortran code implementing the TASS 1.7
theory,  the successor to the Dourneau theory used in the following
code.  TASS probably supplies slightly better accuracy than the
Dourneau theory,  but you would have to be looking well below the
arcsecond level to see much difference.

None of these provides good data for Phoebe.  If you're really interested
in Phoebe,  let me know;  I can provide the source code used in Guide for
Phoebe (and the other irregular satellites of gas giants).  It uses
multipoint interpolation in precomputed ephemerides,  resulting in
wonderful accuracy.  (The precomputed ephemeris resulted from a
numerically integrated orbit.)

   'htc20.cpp' provides ephemerides for Helene,  Telesto,  and Calypso.
'rocks.cpp' provides ephemerides for many other faint inner satellites
of Saturn (and other planets).
*/

            /* Constants defining the angle of a 'fixed' Saturnian equator */
            /* relative to the B1950.0 ecliptic.  The inner four moons are */
            /* all computed relative to the plane of Saturn's equator; you */
            /* then rotate by these two angles, and you're in B1950.0      */
            /* ecliptic coordinates.  (The outer four moons are all in that */
            /* system to begin with.)        */
#define INCL0 (28.0817 * PI / 180.)
#define ASC_NODE0 (168.8112 * PI / 180.)

#define JAPETUS_i0         (18.4602 * PI / 180.)
#define JAPETUS_i0_dot     (-.9518 * PI / 180.)

#define IGNORED_DOUBLE     0.

#define MIMAS           0
#define ENCELADUS       1
#define TETHYS          2
#define DIONE           3
#define RHEA            4
#define TITAN           5
#define HYPERION        6
#define JAPETUS         7
#define PHOEBE          8

#define SECONDS_TO_AU (9.538937 * (PI / 180.) / 3600.)

#define OUTPUT_IN_J2000

struct sat_elems
{
   double jd, semimaj, ecc, gamma, lambda;
   double omega, Omega, epoch;
   double loc[4];
   int sat_no;
};

/* set_ssat_elems( ) is the core part of computing positions for the
satellites of Saturn,  and quite probably the only part of the code
you'll want to grab.  It is essentially just an implementation of
Gerard Dourneau's theory.  The only problem with this theory is that
each satellite has to be handled a little differently... thus the extensive
case statement in this function.  The result,  though,  is a set of
orbital elements for the object.  For the inner four moons,  this is
relative to the equator of Saturn,  and you have to do two rotations to
get a B1950.0 coordinate.  For the outer four moons,  you get B1950.0
elements right away. */

static int
set_ssat_elems(struct sat_elems *elems, struct elements *orbit)
{
   static const long semimaj[9] = { 268180L, 344301, 426393, 545876,
               762277, 1766041, 2140790, 5148431, 18720552 };
   static const short epoch[8] = { 11093, 11093, 11093, 11093, 11093, 11368,
                15020, 9786 };
   static const short ecc0[8] = { 19050, 4850, 0, 2157, 265, 29092, -1,
                                       28298   /*, 163260 */ };
   static const short i_gamma0[8] = { 15630, 262, 10976, 139,
                 3469, 2960, 6435, -1 };
   static const long lam0[9] = {1276400, 2003170, 2853060, 2547120, 3592440,
                  2611582, 1770470, 763852, 2778720 };
   static const double n[9] = { 381.994497, 262.7319002, 190.69791226,
                  131.53493193, 79.6900472, 22.57697855,
                  16.91993829, 4.53795125, -.6541068 };
   static const long big_N0[9] = { 54500, 348000, 111330, 232000, 345000,
                            42000, 94900, 143198, 245998 };
   static const long big_N0_dot[9] = { -36507200, -15195000, -7224410,
                          -3027000, -1005700, -51180, -229200, -3919, -41353 };
   static const long big_P0[9] = { 106100, 309107, 0, 174800, 276590, 276590,
                          69898, 352910, 280165 };
   static const long big_P0_dot[9] = { 36554900, 12344121, 0, 3082000,
                          51180, 51180, -1867088, 11710, -19586 };
   const double sin_gamma0_tan_half_incl = .00151337;
   const double sin_gamma0 = .0060545;
   const double sin_incl1 = .470730;
   int sat = elems->sat_no;
   double t, t_d, t_centuries, t_centuries_squared;

   if (sat == PHOEBE)
   {
      elems->epoch = 2433282.5;
      elems->ecc = .16326;
   }
   else
   {
      elems->epoch = 2400000. + (double)epoch[sat];
      elems->ecc = (double)ecc0[sat] * 1.e-6;
      elems->gamma = (double)i_gamma0[sat] * (PI / 180.) / 10000.;
   }
   t_d = elems->jd - elems->epoch;
   t = t_d / 365.25;
   t_centuries = t / 100.;
   t_centuries_squared = t_centuries * t_centuries;
   if (sat == PHOEBE) {
      elems->gamma = (173.949 - .020 * t) * (PI / 180.);
   }

   elems->semimaj = (double)semimaj[sat] * SECONDS_TO_AU / 10000.;
   elems->lambda = (double)lam0[sat] / 10000. + n[sat] * t_d;
   elems->lambda *= PI / 180;          /* cvt to radians */
   elems->Omega = (double)big_N0[sat] / 1000. +
                               t * (double)big_N0_dot[sat] / 100000.;
   elems->Omega *= PI / 180;          /* cvt to radians */
   elems->omega = (double)big_P0[sat] / 1000. +
                               t * (double)big_P0_dot[sat] / 100000.;
   elems->omega *= PI / 180;          /* cvt to radians */

   switch(sat)
   {
      case MIMAS:
      case TETHYS:
      {
         const double libration_coeffs[3] = {-43.57 * PI / 180.,
                  -.7209 * PI / 180., -.0205 * PI / 180. };
         const double mu0 = 5.095 * PI / 180.;
         const double t0_prime = 1866.39;
         const double mimas_over_tethys = -21.12;
         double mu_delta_tau = mu0 *
                        ((elems->jd-J2000) / 365.25 + 2000. - t0_prime);
         int i;
         double delta_lon = 0.;

         for (i = 0; i < 3; i++) {
            delta_lon += libration_coeffs[i] *
                                     sin((double)(i+i+1) * mu_delta_tau);
         }
         if (sat == TETHYS) {
            delta_lon /= mimas_over_tethys;
         }
         elems->lambda += delta_lon;
      }
      break;

      case ENCELADUS:
      case DIONE:
      {
         const double p2 = 15.4 * (PI / 180.) / 60.;
         const double q2 = 12.59 * (PI / 180.) / 60.;
         const double mu = 74.4 * (PI / 180.);
         const double nu = 32.39 * (PI / 180.);
         const double mu_prime = 134.3 * (PI / 180.);
         const double nu_prime = 92.62 * (PI / 180.);
         const double enceladus_over_dione = -12.;
         double delta_lon;

         delta_lon = p2 * sin(mu + nu * t) +
                     q2 * sin(mu_prime + nu_prime * t);
         if (sat == DIONE) {
            delta_lon /= enceladus_over_dione;
         }
         elems->lambda += delta_lon;
      }
      break;

      case RHEA:
      {
         const double ef = .001;
         const double chi = .0193 * PI / 180.;
         const double pi0 = 342.7 * PI / 180.;
         const double pi_dot = 10.057 * PI / 180.;
         const double big_Nt0 = 42.02 * PI / 180.;
         const double big_Nt_dot = -.5118 * PI / 180.;
         const double Omega1_plus_dOmega = ASC_NODE0 - .0078 * PI / 180.;
         const double Incl1_plus_dIncl = INCL0 - .0455 * PI / 180.;
         const double e0 = .000265;

         const double pi = pi0 + pi_dot * t;
         const double big_N = elems->Omega;
         const double big_Nt = big_Nt0 + big_Nt_dot * t;
         const double e_sin_omega = e0 * sin(pi) + ef * sin(elems->omega);
         const double e_cos_omega = e0 * cos(pi) + ef * cos(elems->omega);
         double perturb_Omega, perturb_incl;

         perturb_incl = sin_gamma0 * cos(big_N) + chi * cos(big_Nt);
         elems->gamma = Incl1_plus_dIncl + perturb_incl;
         perturb_Omega = sin_gamma0 * sin(big_N) + chi * sin(big_Nt);
         elems->Omega = Omega1_plus_dOmega + perturb_Omega / sin_incl1;
         elems->lambda += sin_gamma0_tan_half_incl * sin(big_N);
         elems->omega = atan2(e_sin_omega, e_cos_omega);
         elems->ecc = sqrt(e_sin_omega * e_sin_omega + e_cos_omega * e_cos_omega);
         }
         break;

      case TITAN:
      {
         const double Omega1_plus_dOmega = ASC_NODE0 - .1420 * PI / 180.;
         const double Incl1_plus_dIncl = INCL0 - .6303 * PI / 180.;
         const double g0 = 103.199 * PI / 180.;
         const double beta = .3752 * PI / 180.;

         double big_N = elems->Omega, g;
         double perturb_Omega, perturb_incl;

         elems->lambda += sin_gamma0_tan_half_incl * sin(big_N);
         perturb_Omega = sin_gamma0 * sin(big_N);
         elems->Omega = Omega1_plus_dOmega + perturb_Omega / sin_incl1;
         perturb_incl = sin_gamma0 * cos(big_N);
         elems->gamma = Incl1_plus_dIncl + perturb_incl;
         g = elems->omega - elems->Omega - 4.6 * PI / 180.;
         elems->ecc += beta * elems->ecc * (cos(g + g) - cos(g0 + g0));
         elems->omega += beta * elems->ecc * (sin(g + g) - sin(g0 + g0));
      }
      break;

      case HYPERION:
      {
         const double tau0 =                   92.39 * PI / 180.;
         const double tau_dot =                  .5621071 * PI / 180.;
         const double zeta0 =                 148.19 * PI / 180.;
         const double zeta_dot =              -19.18 * PI / 180.;
         const double phi0 =                  -34.7 * PI / 180.;
         const double phi_dot =               -61.7840 * PI / 180.;
         const double theta0 =                184.8 * PI / 180.;
         const double theta_dot =             -35.41 * PI / 180.;
         const double theta0_prime =          177.3 * PI / 180.;
         const double theta_dot_prime =       -35.41 * PI / 180.;
         const double C_e_zeta =                 .02303;
         const double C_e_2zeta =               -.00212;
         const double C_lam_tau =               9.142 * PI / 180.;
         const double C_lam_zeta =              -.260 * PI / 180.;
         const double C_omega_zeta =          -12.872 * PI / 180.;
         const double C_omega_2zeta =           1.668 * PI / 180.;
         const double C_a_tau =                 -.00003509;
         const double C_a_zeta_plus_tau =       -.00000067;
         const double C_a_zeta_minus_tau =       .00000071;
         const double C_e_tau =                 -.004099;
         const double C_e_3zeta =                .000151;
         const double C_e_zeta_plus_tau =       -.000167;
         const double C_e_zeta_minus_tau =       .000235;
         const double C_lam_2zeta =             -.0098 * PI / 180.;
         const double C_lam_zeta_plus_tau =      .2275 * PI / 180.;
         const double C_lam_zeta_minus_tau =     .2112 * PI / 180.;
         const double C_lam_phi =               -.0303 * PI / 180.;
         const double C_omega_tau =             -.4457 * PI / 180.;
         const double C_omega_3zeta =           -.2419 * PI / 180.;
         const double C_omega_zeta_plus_tau =   -.2657 * PI / 180.;
         const double C_omega_zeta_minus_tau =  -.3573 * PI / 180.;
         const double C_incl_theta =             .0180 * PI / 180.;
         const double C_Omega_theta_prime =      .0168 * PI / 180.;
         const double big_Nt0 =                42.02 * PI / 180.;
         const double big_Nt_dot =              -.5118 * PI / 180.;
         const double hy_gamma0 =                .6435 * PI / 180.;
         const double sin_hy_gamma0 =             .011231;

                                       /* from (45), p 59 */
         const double Omega1_plus_dOmega =    ASC_NODE0 - .747 * PI / 180.;
         const double Incl1_plus_dIncl =          INCL0 - .13 * PI / 180.;
/*       const double Omega1_plus_dOmega =    ASC_NODE0 - .0078 * PI / 180.; */
/*       const double Incl1_plus_dIncl =          INCL0 - .0455 * PI / 180.; */
         const double sin_Incl1_plus_dIncl =        0.468727;
         const double tan_half_Incl1_plus_dIncl =   0.248880;

                                       /* from (44), p 59 */
         const double big_T = (elems->jd - 2442000.5) / 365.25;
         const double t_T = (elems->jd - 2411368.0) / 365.25;
         const double big_N = elems->Omega;
         const double big_Nt = big_Nt0 + big_Nt_dot * t_T;
         const double tau = tau0 + tau_dot * t_d;
         const double zeta = zeta0 + zeta_dot * t;
         const double phi = phi0 + phi_dot * t;
         const double lambda_s = (176. + 12.22 * t) * PI / 180.;
         const double b_s = (8. + 24.44 * t) * PI / 180.;
         const double d_s = b_s + 5. * PI / 180.;

         const double theta = theta0 + theta_dot * big_T;
         const double theta_prime = theta0_prime + theta_dot_prime * big_T;
         double arg;

         elems->ecc = .103458;

         elems->gamma = sin_hy_gamma0 * cos( big_N)
                           + .315 * (PI / 180.) * cos( big_Nt)
                           - .018 * (PI / 180.) * cos( d_s)
                           + C_incl_theta * cos( theta);
         elems->gamma += Incl1_plus_dIncl;

         arg = sin( big_N);
         elems->Omega = sin_hy_gamma0 * arg
                           + .315 * (PI / 180.) * sin( big_Nt)
                           - .018 * (PI / 180.) * sin( d_s)
                           + C_Omega_theta_prime * sin( theta_prime);
         elems->Omega = Omega1_plus_dOmega
                                 + elems->Omega / sin_Incl1_plus_dIncl;
         elems->lambda += hy_gamma0 * tan_half_Incl1_plus_dIncl * arg;
         elems->omega += hy_gamma0 * tan_half_Incl1_plus_dIncl * arg;
         arg = sin( tau);
         elems->lambda += C_lam_tau * arg
                         + .007 * (PI / 180.) * sin( tau + tau)
                         - .014 * (PI / 180.) * sin( 3. * tau)
                         - .013 * (PI / 180.) * sin( lambda_s)
                         + .017 * (PI / 180.) * sin( b_s)
                         + C_lam_phi * sin( phi);
         elems->omega += C_omega_tau * arg
                      + C_omega_3zeta * sin( 3. * zeta);
         arg = sin( zeta + tau);
         elems->lambda += C_lam_zeta_plus_tau * arg;
         elems->omega += C_omega_zeta_plus_tau * arg;
         arg = sin( zeta - tau);
         elems->lambda += C_lam_zeta_minus_tau * arg;
         elems->omega += C_omega_zeta_minus_tau * arg;
         arg = sin( zeta);
         elems->lambda += C_lam_zeta * arg;
         elems->omega += C_omega_zeta * arg;
         arg = sin( zeta + zeta);
         elems->lambda += C_lam_2zeta * arg;
         elems->omega += C_omega_2zeta * arg;

         arg = cos( tau);
         elems->semimaj += C_a_tau * arg * SECONDS_TO_AU;
         elems->ecc += C_e_tau * arg;
         arg = cos( zeta + tau);
         elems->semimaj += C_a_zeta_plus_tau * arg * SECONDS_TO_AU;
         elems->ecc += C_e_zeta_plus_tau * arg;
         arg = cos( zeta - tau);
         elems->semimaj += C_a_zeta_minus_tau * arg * SECONDS_TO_AU;
         elems->ecc += C_e_zeta_minus_tau * arg
                      + C_e_zeta * cos( zeta)
                      + C_e_2zeta * cos( zeta + zeta)
                      + C_e_3zeta * cos( 3. * zeta)
                      + .00013 * cos( phi);
      }
      break;

      case JAPETUS:
      {
         elems->gamma = JAPETUS_i0 + JAPETUS_i0_dot * t_centuries;
         elems->gamma += (-.072 + .0054 * t_centuries) * t_centuries_squared
                                 * PI / 180.;
         elems->Omega += (.116 + .008 * t_centuries) * t_centuries_squared
                                 * PI / 180.;
         elems->ecc += .001156 * t_centuries;

                              /* The following corrections are from p. 61, */
                              /* G. Dourneau,  group 50: */
         const double big_T = (elems->jd - 2415020.) / 36525.;
         const double t_diff = elems->jd - 2411368.;
         const double lam_s =         (267.263 + 1222.114 * big_T) * (PI / 180.);
         const double omega_s_tilde = ( 91.796 +     .562 * big_T) * (PI / 180.);
         const double psi =           (  4.367 -     .195 * big_T) * (PI / 180.);
         const double theta =         (146.819 -    3.918 * big_T) * (PI / 180.);
         const double lam_t =         (261.319 + 22.576974 * t_diff) * (PI / 180.);
         const double omega_t_tilde = (277.102 +   .001389 * t_diff) * (PI / 180.);
         const double phi =           ( 60.470 +    1.521 * big_T) * (PI / 180.);
         const double Phi =           (205.055 -    2.091 * big_T) * (PI / 180.);

                              /* group 49: */
         const double l = elems->lambda - elems->omega;
         const double g  = elems->omega - elems->Omega - psi;
         const double g1 = elems->omega - elems->Omega - phi;
         const double ls = lam_s - omega_s_tilde;
         const double gs = omega_s_tilde - theta;
         const double lt = lam_t - omega_t_tilde;
         const double gt = omega_t_tilde - Phi;
         const double ls_plus_gs_2 = 2. * (ls + gs);
         const double ls_gs_minus_g_2 = ls_plus_gs_2 - 2. * g;
         const double lt_plus_gt = lt + gt;
         const double lt_gt_minus_g1 = lt_plus_gt - g1;


                              /* group 48: */
         const double d_a = elems->semimaj * (7.87 * cos(2. * l - ls_gs_minus_g_2)
                                   + 98.79 * cos(l - lt_gt_minus_g1));
         const double d_e = -140.97 * cos(g1 - gt)
                             + 37.33 * cos(ls_gs_minus_g_2)
                             + 11.80 * cos(l - ls_gs_minus_g_2)
                             + 24.08 * cos(l)
                             + 28.49 * cos(l + l - lt_gt_minus_g1)
                             + 61.90 * cos(lt_gt_minus_g1);
         const double d_omega = .08077 * sin(g1 - gt)
                                + .02139 * sin(ls_gs_minus_g_2)
                                - .00676 * sin(l - ls_gs_minus_g_2)
                                + .01380 * sin(l)
                                + .01632 * sin(l + l - lt_gt_minus_g1)
                                + .03547 * sin(lt_gt_minus_g1);
         const double d_lambda = -.04299 * sin(l - lt_gt_minus_g1)
                                  -.00789 * sin(2. * l - ls_gs_minus_g_2)
                                  -.06312 * sin(ls)
                                  -.00295 * sin(ls + ls)
                                  -.02231 * sin(ls_plus_gs_2)
                                  +.00650 * sin(ls_plus_gs_2 + phi);
         const double d_incl = .04204 * cos(ls_plus_gs_2 + phi)
                               +.00235 * cos(l + g1 + lt_plus_gt + phi)
                               +.00360 * cos(l - lt_gt_minus_g1 + phi);
         const double d_Omega = .04204 * sin(ls_plus_gs_2 + phi)
                               +.00235 * sin(l + g1 + lt_plus_gt + phi)
                               +.00358 * sin(l - lt_gt_minus_g1 + phi);

         elems->semimaj += d_a * 1.e-5;
         elems->omega += d_omega * (PI / 180.) / elems->ecc;
         elems->Omega += d_Omega * (PI / 180.) / sin( elems->gamma);
         elems->ecc += d_e * 1.e-5;
         elems->lambda += d_lambda * (PI / 180.);
         elems->gamma += d_incl * (PI / 180.);
      }
      break;

      case PHOEBE:
      {
                              /* The elements given for Phoebe in the     */
                              /* _Explanatory Suppl_ run the 'wrong way'. */
                              /* Either the retrograde orbit confused them,  */
                              /* or they chose to swap conventions. */
         elems->lambda = 2. * elems->Omega - elems->lambda;
         elems->omega  = 2. * elems->Omega - elems->omega;
      }
      break;
      default:
         break;
   }

   if (sat < RHEA)
   {
      elems->Omega -= ASC_NODE0;
      elems->omega -= ASC_NODE0;
      elems->lambda -= ASC_NODE0;
   }

   orbit->mean_anomaly = elems->lambda - elems->omega;
   orbit->mean_anomaly = fmod( orbit->mean_anomaly, TWO_PI);
   if (orbit->mean_anomaly > PI)
      orbit->mean_anomaly -= TWO_PI;
   if (orbit->mean_anomaly <-PI)
      orbit->mean_anomaly += TWO_PI;

   orbit->major_axis = elems->semimaj;
   orbit->q = elems->semimaj * (1. - elems->ecc);
   orbit->ecc = elems->ecc;
   orbit->incl = elems->gamma;
   orbit->arg_per = elems->omega - elems->Omega;
   orbit->asc_node = elems->Omega;
   return( 0);
}

/*
   This is the function I use to get Cartesian coordinates of date,
Saturnicentric,  for a satellite of Saturn.  You'll probably have your
own functions to do most of this,  except for the above set_ssat_elems( )
function.  As I remarked for that function,  you get orbital elements
for a satellite through Dourneau's theory;  then you compute a Cartesian
coordinate;  and if it's one of the four inner satellites (Mimas,
Enceladus, Tethys,  or Rhea),  you have to rotate it from Saturn's
equator to B1950.

   At that point,  you've got B1950 ecliptic coordinates,  which are
then rotated to B1950 equatorial coordinates.  The default then is
to precess them to equatorial coordinates of date;  then rotate back
to ecliptic coordinates of date,  and you're all set.  That's just
because Meeus' formulae formulae are all in ecliptic coords of date,
and it was convenient to go for consistency with the rest of my
existing code.

   HOWEVER,  if you #define OUTPUT_IN_J2000,  then the vector will
instead get precessed to equatorial J2000,  then rotated to ecliptic
J2000.
*/

static int
calc_ssat_loc(const double t, double *ssat,
              const int sat_wanted, const long precision)
{
   struct sat_elems elems;
   struct elements orbit;
   double matrix[9];
   const double t_years = (t - J2000) / 365.25;

   if (precision == -1L)         /* just checking version # */
      return (1);
   if (sat_wanted < 0 || sat_wanted > PHOEBE)
      return (-1);
   elems.jd = t;
   elems.sat_no = sat_wanted;
   set_ssat_elems(&elems, &orbit);

   setup_orbit_vectors(&orbit);
   kepler_pos_vel(&orbit, IGNORED_DOUBLE, elems.loc, NULL);

   if(sat_wanted < RHEA)    /* inner 4 satellites are returned in Saturnic */
   {                            /*  coords so gotta rotate to B1950.0 */
      rotate_vector( elems.loc, INCL0, 0);
      rotate_vector( elems.loc, ASC_NODE0, 2);
   }
                        /* After above,  elems.loc is ecliptic 1950 coords */
   rotate_vector( elems.loc, OBLIQUITY_1950, 0);
                        /* Now,  elems.loc is equatorial 1950 coords */

#ifdef OUTPUT_IN_J2000
   setup_precession(matrix, 1950., 2000);
   precess_vector(matrix, elems.loc, ssat);
                        /* Now,  ssats is equatorial J2000... */
   rotate_vector(ssat, -OBLIQUITY_2000, 0);
                        /* And now,  ssats is ecliptical J2000 */
#else
   setup_precession(matrix, 1950., 2000. + t_years);
   precess_vector(matrix, elems.loc, ssat);
                        /* Now,  ssats is equatorial of epoch coords */
   rotate_vector(ssat, -mean_obliquity( t_years / 100.), 0);
                        /* And now,  ssats is ecliptical of epoch coords */
                        /* (which is what we really want anyway) */
#endif
   return( 0);
}

LPoint3d
dourneau_sat_pos(double jd, int body)
{
  double loc[3];
  calc_ssat_loc(jd, loc, body, 0);
  return LPoint3d(loc[0], loc[1], loc[2]) * AU_IN_KM;
}
