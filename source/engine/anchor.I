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
AnchorBase::get_albedo(void) const
{
  return _albedo;
}


void
AnchorBase::set_albedo(double albedo)
{
  _albedo = albedo;
}


double
AnchorBase::get_intrinsic_luminosity(void) const
{
  return _intrinsic_luminosity;
}


void
AnchorBase::set_intrinsic_luminosity(double intrinsic_luminosity)
{
  _intrinsic_luminosity = intrinsic_luminosity;
}


double
AnchorBase::get_reflected_luminosity(void) const
{
  return _reflected_luminosity;
}


double
AnchorBase::get_cached_point_radiance(void) const
{
  return _point_radiance;
}

double
AnchorBase::get_radiant_flux(void) const
{
  return _intrinsic_luminosity + _reflected_luminosity;
}


double
AnchorBase::get_point_radiance(double distance) const
{
  return (_intrinsic_luminosity + _reflected_luminosity) / (4 * M_PI * distance * distance * 1000 * 1000);
}
