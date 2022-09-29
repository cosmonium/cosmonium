/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2022 Laurent Deru.
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


double
StellarAnchor::get_albedo(void) const
{
  return _albedo;
}


void
StellarAnchor::set_albedo(double albedo)
{
  _albedo = albedo;
}


double
StellarAnchor::get_intrinsic_luminosity(void) const
{
  return _intrinsic_luminosity;
}


void
StellarAnchor::set_intrinsic_luminosity(double intrinsic_luminosity)
{
  _intrinsic_luminosity = intrinsic_luminosity;
}


double
StellarAnchor::get_reflected_luminosity(void) const
{
  return _reflected_luminosity;
}


double
StellarAnchor::get_point_radiance(void) const
{
  return _point_radiance;
}
