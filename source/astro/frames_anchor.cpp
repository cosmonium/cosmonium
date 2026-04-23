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

#include "frames_anchor.h"
#include "anchor.h"
#include "astro.h"

TypeHandle AnchorReferenceFrame::_type_handle;

AnchorReferenceFrame::AnchorReferenceFrame(AnchorBase *anchor) :
    anchor(anchor)
{
}

AnchorReferenceFrame::AnchorReferenceFrame(AnchorReferenceFrame const &other) :
    anchor(other.anchor)
{
}

PT(ReferenceFrame)
AnchorReferenceFrame::make_copy(void) const
{
  return new AnchorReferenceFrame(*this);
}

AnchorBase *
AnchorReferenceFrame::get_anchor(void) const
{
  return anchor;
}

void
AnchorReferenceFrame::set_anchor(AnchorBase *anchor)
{
  this->anchor = anchor;
}

LPoint3d
AnchorReferenceFrame::get_center(void)
{
  return anchor->get_local_position();
}

LPoint3d
AnchorReferenceFrame::get_absolute_reference_point(void)
{
  return anchor->get_absolute_reference_point();
}

LQuaterniond
AnchorReferenceFrame::get_orientation(void)
{
  return anchor->get_absolute_orientation();
}

TypeHandle J2000EclipticReferenceFrame::_type_handle;

J2000EclipticReferenceFrame::J2000EclipticReferenceFrame(AnchorBase *anchor) :
    AnchorReferenceFrame(anchor)
{
}

J2000EclipticReferenceFrame::J2000EclipticReferenceFrame(J2000EclipticReferenceFrame const &other) :
    AnchorReferenceFrame(other.anchor)
{
}

PT(ReferenceFrame)
J2000EclipticReferenceFrame::make_copy(void) const
{
  return new J2000EclipticReferenceFrame(*this);
}

LQuaterniond
J2000EclipticReferenceFrame::get_orientation(void)
{
  return LQuaterniond::ident_quat();
}

TypeHandle J2000EquatorialReferenceFrame::_type_handle;

J2000EquatorialReferenceFrame::J2000EquatorialReferenceFrame(AnchorBase *anchor) :
    AnchorReferenceFrame(anchor)
{
}

J2000EquatorialReferenceFrame::J2000EquatorialReferenceFrame(J2000EquatorialReferenceFrame const &other) :
    AnchorReferenceFrame(other.anchor)
{
}

PT(ReferenceFrame)
J2000EquatorialReferenceFrame::make_copy(void) const
{
  return new J2000EquatorialReferenceFrame(*this);
}

LQuaterniond
J2000EquatorialReferenceFrame::get_orientation(void)
{
  LQuaterniond orientation;
  orientation.set_from_axis_angle_rad(-to_rad(J2000_Obliquity), LVector3d::unit_x());
  return orientation;
}

TypeHandle CelestialReferenceFrame::_type_handle;

CelestialReferenceFrame::CelestialReferenceFrame(AnchorBase *anchor,
    double right_ascension,
    double declination,
    double longitude_at_node) :
    AnchorReferenceFrame(anchor),
    _right_ascension(right_ascension),
    _declination(declination),
    _longitude_at_node(longitude_at_node)
{
  update_orientation();
}

CelestialReferenceFrame::CelestialReferenceFrame(CelestialReferenceFrame const &other) :
    AnchorReferenceFrame(other.anchor),
    _right_ascension(other._right_ascension),
    _declination(other._declination),
    _longitude_at_node(other._longitude_at_node)
{
  update_orientation();
}

PT(ReferenceFrame)
CelestialReferenceFrame::make_copy(void) const
{
  return new CelestialReferenceFrame(*this);
}

void
CelestialReferenceFrame::update_orientation(void)
{
  double inclination = M_PI / 2 - to_rad(_declination);
  double ascending_node = to_rad(_right_ascension) + M_PI / 2;

  LQuaterniond inclination_quat;
  inclination_quat.set_from_axis_angle_rad(inclination, LVector3d::unit_x());
  LQuaterniond ascending_node_quat;
  ascending_node_quat.set_from_axis_angle_rad(ascending_node, LVector3d::unit_z());
  LQuaterniond longitude_quat;
  longitude_quat.set_from_axis_angle_rad(to_rad(_longitude_at_node), LVector3d::unit_z());
  LQuaterniond equatorial_orientation;
  equatorial_orientation.set_from_axis_angle_rad(-to_rad(J2000_Obliquity), LVector3d::unit_x());
  orientation = longitude_quat * inclination_quat * ascending_node_quat * equatorial_orientation;
}

LQuaterniond
CelestialReferenceFrame::get_orientation(void)
{
  return orientation;
}

double
CelestialReferenceFrame::get_right_ascension(void) const
{
  return _right_ascension;
}

void
CelestialReferenceFrame::set_right_ascension(double ra)
{
  _right_ascension = ra;
  update_orientation();
}

double
CelestialReferenceFrame::get_declination(void) const
{
  return _declination;
}

void
CelestialReferenceFrame::set_declination(double decl)
{
  _declination = decl;
  update_orientation();
}

double
CelestialReferenceFrame::get_longitude_at_node(void) const
{
  return _longitude_at_node;
}

void
CelestialReferenceFrame::set_longitude_at_node(double lon)
{
  _longitude_at_node = lon;
  update_orientation();
}
