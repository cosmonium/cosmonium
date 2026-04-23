/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2024 Laurent Deru.
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

#include "frames_base.h"
#include "astro.h"

TypeHandle ReferenceFrame::_type_handle;

ReferenceFrame::~ReferenceFrame(void)
{
}

LPoint3d
ReferenceFrame::get_absolute_position(LPoint3d frame_position)
{
  return get_absolute_reference_point() + get_local_position(frame_position);
}

LPoint3d
ReferenceFrame::get_local_position(LPoint3d frame_position)
{
  return get_center() + get_orientation().xform(frame_position);
}

LPoint3d
ReferenceFrame::get_frame_position(LPoint3d local_position)
{
  return get_orientation().conjugate().xform(local_position - get_center());
}

LQuaterniond
ReferenceFrame::get_absolute_orientation(LQuaterniond frame_orientation)
{
  return frame_orientation * get_orientation();
}

LQuaterniond
ReferenceFrame::get_frame_orientation(LQuaterniond absolute_orientation)
{
  return absolute_orientation * get_orientation().conjugate();
}

TypeHandle J2000BarycentricEclipticReferenceFrame::_type_handle;

J2000BarycentricEclipticReferenceFrame::J2000BarycentricEclipticReferenceFrame(void)
{
}

J2000BarycentricEclipticReferenceFrame::J2000BarycentricEclipticReferenceFrame(J2000BarycentricEclipticReferenceFrame const &other)
{
}

PT(ReferenceFrame)
J2000BarycentricEclipticReferenceFrame::make_copy(void) const
{
  return new J2000BarycentricEclipticReferenceFrame(*this);
}

LPoint3d
J2000BarycentricEclipticReferenceFrame::get_center(void)
{
  return LPoint3d(0.0);
}

LQuaterniond
J2000BarycentricEclipticReferenceFrame::get_orientation(void)
{
  return LQuaterniond::ident_quat();
}

LPoint3d
J2000BarycentricEclipticReferenceFrame::get_absolute_reference_point(void)
{
  return LPoint3d(0.0);
}

TypeHandle J2000BarycentricEquatorialReferenceFrame::_type_handle;

J2000BarycentricEquatorialReferenceFrame::J2000BarycentricEquatorialReferenceFrame(void)
{
}

J2000BarycentricEquatorialReferenceFrame::J2000BarycentricEquatorialReferenceFrame(J2000BarycentricEquatorialReferenceFrame const &other)
{
}

PT(ReferenceFrame)
J2000BarycentricEquatorialReferenceFrame::make_copy(void) const
{
  return new J2000BarycentricEquatorialReferenceFrame(*this);
}

LPoint3d
J2000BarycentricEquatorialReferenceFrame::get_center(void)
{
  return LPoint3d(0.0);
}

LQuaterniond
J2000BarycentricEquatorialReferenceFrame::get_orientation(void)
{
  LQuaterniond orientation;
  orientation.set_from_axis_angle_rad(-to_rad(J2000_Obliquity), LVector3d::unit_x());
  return orientation;
}

LPoint3d
J2000BarycentricEquatorialReferenceFrame::get_absolute_reference_point(void)
{
  return LPoint3d(0.0);
}
