/* miscell.cpp: misc. astronomy-related functions

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
#include <string.h>
#include "lunar.h"

/* It's embarrassingly common to find out that,  after roundoff errors,
   you're attempting to take the arccosine or arcsine of +/- 1.0000001,
   resulting in a math exception.  Use of acose( ) and asine( ) lets you
   slip around such difficulties.

      There are two reasons to be careful about this.  First,  if a for-real
   error results in arg=78,  acose( ) (for example) will silently truncate it
   to 1 and return 0.  Second,  if you're sometimes getting 1+(1e-14),  you're
   probably also sometimes getting 1-(1e-14).  In this range,  the precision
   of the acos and asin functions is horrible,  and deformed values will be
   returned silently.  It's better,  in such cases,  to give some thought as
   to a better way to get the answer you want.  Look,  for example,  in
   'dist_pa.cpp' where asin is used in one domain and acos in the other,
   avoiding areas where bad values would be generated.
*/

double
acose(const double arg)
{
   if (arg >= 1.)
      return (0.);
   if (arg <= -1.)
      return (PI);
   return (acos(arg));
}

double
asine(const double arg)
{
   if (arg >= 1.)
      return (PI / 2);
   if (arg <= -1.)
      return (-PI / 2.);
   return (asin(arg));
}

void
set_identity_matrix(double *matrix)
{
   int i;

   for( i = 0; i < 9; i++)
      matrix[i] = ((i & 3) ? 0. : 1.);
}

          /* Inverting an orthonormal matrix happens to be an unusually   */
          /* simple job:  swap rows and columns,  and you're in business. */
          /* This really ought to be just called 'transpose_matrix'.      */

#define SWAP( A, B, TEMP)  { TEMP = A;  A = B;  B = TEMP; }

void
invert_orthonormal_matrix(double *matrix)
{
   double temp;

   SWAP( matrix[1], matrix[3], temp);
   SWAP( matrix[2], matrix[6], temp);
   SWAP( matrix[5], matrix[7], temp);
}

void
rotate_vector(double *v, const double angle, const int axis)
{
   const double sin_ang = sin( angle), cos_ang = cos( angle);
   const int a = (axis + 1) % 3, b = (axis + 2) % 3;
   const double temp = v[a] * cos_ang - v[b] * sin_ang;

   v[b] = v[b] * cos_ang + v[a] * sin_ang;
   v[a] = temp;
}

void
pre_spin_matrix(double *v1, double *v2, const double angle)
{
   const double sin_ang = sin( angle);
   const double cos_ang = cos( angle);
   int i;

   for( i = 3; i; i--)
      {
      const double tval = *v1 * cos_ang - *v2 * sin_ang;

      *v2 = *v2 * cos_ang + *v1 * sin_ang;
      *v1 = tval;
      v1 += 3;
      v2 += 3;
      }
}

void spin_matrix(double *v1, double *v2, const double angle)
{
   const double sin_ang = sin( angle);
   const double cos_ang = cos( angle);
   int i;

   for( i = 3; i; i--)
      {
      const double tval = *v1 * cos_ang - *v2 * sin_ang;

      *v2 = *v2 * cos_ang + *v1 * sin_ang;
      *v1++ = tval;
      v2++;
      }
}

void
polar3_to_cartesian(double *vect, const double lon, const double lat)
{
   double clat = cos( lat);

   *vect++ = cos( lon) * clat;
   *vect++ = sin( lon) * clat;
   *vect   = sin( lat);
}

double
vector3_length(const double *vect)
{
   return (sqrt(vect[0] * vect[0] + vect[1] * vect[1] + vect[2] * vect[2]));
}

void
vector_cross_product(double *xprod, const double *a, const double *b)
{
   xprod[0] = a[1] * b[2] - a[2] * b[1];
   xprod[1] = a[2] * b[0] - a[0] * b[2];
   xprod[2] = a[0] * b[1] - a[1] * b[0];
}
