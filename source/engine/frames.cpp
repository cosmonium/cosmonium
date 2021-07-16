/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2021 Laurent Deru.
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

#include "frames.h"
#include "anchors.h"
#include "astro.h"
#include "orbits.h"
#include "dcast.h"

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

TypeHandle AnchorReferenceFrame::_type_handle;

AnchorReferenceFrame::AnchorReferenceFrame(AnchorBase *anchor) :
    anchor(anchor)
{
}

AnchorReferenceFrame::AnchorReferenceFrame(AnchorReferenceFrame const &other) :
    anchor(other.anchor)
{
}

AnchorBase *
AnchorReferenceFrame::get_anchor(void)
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
    right_ascension(right_ascension),
    declination(declination),
    longitude_at_node(longitude_at_node)
{
  update_orientation();
}

CelestialReferenceFrame::CelestialReferenceFrame(CelestialReferenceFrame const &other) :
    AnchorReferenceFrame(other.anchor),
    right_ascension(other.right_ascension),
    declination(other.declination),
    longitude_at_node(other.longitude_at_node)
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
  double inclination = M_PI / 2 - to_rad(declination);
  double ascending_node = to_rad(right_ascension) + M_PI / 2;

  LQuaterniond inclination_quat;
  inclination_quat.set_from_axis_angle_rad(inclination, LVector3d::unit_x());
  LQuaterniond ascending_node_quat;
  ascending_node_quat.set_from_axis_angle_rad(ascending_node, LVector3d::unit_z());
  LQuaterniond longitude_quat;
  longitude_quat.set_from_axis_angle_rad(to_rad(longitude_at_node), LVector3d::unit_z());
  LQuaterniond equatorial_orientation;
  equatorial_orientation.set_from_axis_angle_rad(-to_rad(J2000_Obliquity), LVector3d::unit_x());
  orientation = longitude_quat * inclination_quat * ascending_node_quat * equatorial_orientation;
}

LQuaterniond
CelestialReferenceFrame::get_orientation(void)
{
  return orientation;
}

TypeHandle OrbitReferenceFrame::_type_handle;

OrbitReferenceFrame::OrbitReferenceFrame(AnchorBase *anchor) :
    AnchorReferenceFrame(anchor)
{
}

OrbitReferenceFrame::OrbitReferenceFrame(OrbitReferenceFrame const &other) :
    AnchorReferenceFrame(other.anchor)
{
}

PT(ReferenceFrame)
OrbitReferenceFrame::make_copy(void) const
{
  return new OrbitReferenceFrame(*this);
}

LQuaterniond
OrbitReferenceFrame::get_orientation(void)
{
  return DCAST(StellarAnchor, anchor)->get_orbit()->get_frame()->get_orientation();
}

TypeHandle EquatorialReferenceFrame::_type_handle;

EquatorialReferenceFrame::EquatorialReferenceFrame(AnchorBase *anchor) :
    AnchorReferenceFrame(anchor)
{
}

EquatorialReferenceFrame::EquatorialReferenceFrame(EquatorialReferenceFrame const &other) :
    AnchorReferenceFrame(other.anchor)
{
}

PT(ReferenceFrame)
EquatorialReferenceFrame::make_copy(void) const
{
  return new EquatorialReferenceFrame(*this);
}

LQuaterniond
EquatorialReferenceFrame::get_orientation(void)
{
  return anchor->get_equatorial_rotation();
}

TypeHandle SynchroneReferenceFrame::_type_handle;

SynchroneReferenceFrame::SynchroneReferenceFrame(AnchorBase *anchor) :
    AnchorReferenceFrame(anchor)
{
}

SynchroneReferenceFrame::SynchroneReferenceFrame(SynchroneReferenceFrame const &other) :
    AnchorReferenceFrame(other.anchor)
{
}

PT(ReferenceFrame)
SynchroneReferenceFrame::make_copy(void) const
{
  return new SynchroneReferenceFrame(*this);
}

LQuaterniond
SynchroneReferenceFrame::get_orientation(void)
{
  return anchor->get_sync_rotation();
}

TypeHandle RelativeReferenceFrame::_type_handle;

RelativeReferenceFrame::RelativeReferenceFrame(ReferenceFrame *parent_frame, LPoint3d position, LQuaterniond orientation) :
    parent_frame(parent_frame),
    frame_position(position),
    frame_orientation(orientation)
{
}

RelativeReferenceFrame::RelativeReferenceFrame(RelativeReferenceFrame const &other) :
    parent_frame(other.parent_frame),
    frame_position(frame_position),
    frame_orientation(frame_orientation)
{
}

PT(ReferenceFrame)
RelativeReferenceFrame::make_copy(void) const
{
  return new RelativeReferenceFrame(*this);
}

LPoint3d
RelativeReferenceFrame::get_center(void)
{
  return parent_frame->get_local_position(frame_position);
}

LQuaterniond
RelativeReferenceFrame::get_orientation(void)
{
  return parent_frame->get_absolute_orientation(frame_orientation);
}


LPoint3d
RelativeReferenceFrame::get_absolute_reference_point(void)
{
  return parent_frame->get_absolute_reference_point();
}
