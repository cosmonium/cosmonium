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

#include "rotations.h"
#include "frames.h"
#include "stellarAnchor.h"
#include "orbits.h"
#include "astro.h"

TypeHandle RotationBase::_type_handle;

RotationBase::RotationBase(ReferenceFrame *frame) :
  frame(frame)
{
}

RotationBase::~RotationBase(void)
{
}

ReferenceFrame *
RotationBase::get_frame(void)
{
  return frame;
}

void
RotationBase::set_frame(ReferenceFrame *frame)
{
  this->frame = frame;
}

LQuaterniond
RotationBase::get_equatorial_orientation_at(double time)
{
  return frame->get_absolute_orientation(get_frame_equatorial_orientation_at(time));
}


LQuaterniond
RotationBase::get_absolute_rotation_at(double time)
{
  return frame->get_absolute_orientation(get_frame_rotation_at(time));
}

bool
RotationBase::is_flipped(void) const
{
  return false;
}

LQuaterniond
RotationBase::calc_orientation(double a, double d, bool flipped) const
{
  double inclination = M_PI / 2 - to_rad(d);
  double ascending_node = to_rad(a) + M_PI / 2;

  if (flipped) {
    inclination += M_PI;
  }
  LQuaterniond inclination_quat;
  inclination_quat.set_from_axis_angle_rad(inclination, LVector3d::unit_x());
  LQuaterniond ascending_node_quat;
  ascending_node_quat.set_from_axis_angle_rad(ascending_node,  LVector3d::unit_z());
  return inclination_quat * ascending_node_quat;
}

TypeHandle CachedRotationBase::_type_handle;

CachedRotationBase::CachedRotationBase(ReferenceFrame *frame) :
    RotationBase(frame),
    last_orientation_time(INFINITY),
    last_rotation_time(INFINITY)
{
}

LQuaterniond
CachedRotationBase::get_frame_equatorial_orientation_at(
    double time)
{
  if (last_orientation_time != time) {
    last_orientation_time = time;
    last_orientation = calc_frame_equatorial_orientation_at(time);
  }
  return last_orientation;
}

LQuaterniond
CachedRotationBase::get_frame_rotation_at(double time)
{
  if (last_rotation_time != time) {
    last_rotation_time = time;
    last_rotation = calc_frame_rotation_at(time);
  }
  return last_rotation;
}

TypeHandle FixedRotation::_type_handle;

FixedRotation::FixedRotation(LQuaterniond rotation, ReferenceFrame *frame) :
    RotationBase(frame),
    rotation(rotation)
{
}

FixedRotation::FixedRotation(FixedRotation const &other) :
    RotationBase(other.frame),
    rotation(other.rotation)
{
}

PT(RotationBase)
FixedRotation::make_copy(void) const
{
  return new FixedRotation(*this);
}

LQuaterniond
FixedRotation::get_frame_equatorial_orientation_at(double time)
{
  return rotation;
}

LQuaterniond
FixedRotation::get_frame_rotation_at(double time)
{
  return rotation;
}

void
FixedRotation::set_frame_rotation(LQuaterniond rotation)
{
  this->rotation = rotation;
}

TypeHandle UnknownRotation::_type_handle;

UnknownRotation::UnknownRotation(void) :
    RotationBase(new J2000BarycentricEclipticReferenceFrame())
{
}

UnknownRotation::UnknownRotation(UnknownRotation const &other) :
    RotationBase(other.frame)
{
}

PT(RotationBase)
UnknownRotation::make_copy(void) const
{
  return new UnknownRotation(*this);
}

LQuaterniond
UnknownRotation::get_frame_equatorial_orientation_at(double time)
{
  return LQuaterniond::ident_quat();
}

LQuaterniond
UnknownRotation::get_frame_rotation_at(double time)
{
  return LQuaterniond::ident_quat();
}

TypeHandle UniformRotation::_type_handle;

UniformRotation::UniformRotation(LQuaterniond equatorial_orientation,
    double mean_motion,
    double meridian_angle,
    double epoch,
    ReferenceFrame *frame) :
    RotationBase(frame),
    equatorial_orientation(equatorial_orientation),
    mean_motion(mean_motion),
    meridian_angle(meridian_angle),
    epoch(epoch)
{
}

UniformRotation::UniformRotation(UniformRotation const &other) :
    RotationBase(other.frame),
    equatorial_orientation(other.equatorial_orientation),
    mean_motion(other.mean_motion),
    meridian_angle(other.meridian_angle),
    epoch(other.epoch)
{
}

PT(RotationBase)
UniformRotation::make_copy(void) const
{
  return new UniformRotation(*this);
}

LQuaterniond
UniformRotation::get_frame_equatorial_orientation_at(double time)
{
  return equatorial_orientation;
}

LQuaterniond
UniformRotation::get_frame_rotation_at(double time)
{
  double angle = (time - epoch) * mean_motion + meridian_angle;
  LQuaterniond rotation;
  if (mean_motion < 0) {
      angle = -angle;
  }
  rotation.set_from_axis_angle_rad(angle, LVector3d::unit_z());
  return rotation * get_frame_equatorial_orientation_at(time);
}

double
UniformRotation::get_period(void) const
{
  return 2 * M_PI / mean_motion;
}

bool
UniformRotation::is_flipped(void) const
{
  return mean_motion < 0;
}

TypeHandle SynchronousRotation::_type_handle;

SynchronousRotation::SynchronousRotation(LQuaterniond equatorial_orientation,
    double meridian_angle,
    double epoch,
    ReferenceFrame *frame) :
    RotationBase(frame),
    equatorial_orientation(equatorial_orientation),
    parent_body(nullptr),
    meridian_angle(meridian_angle),
    epoch(epoch)
{
}

SynchronousRotation::SynchronousRotation(SynchronousRotation const &other) :
    RotationBase(other.frame),
    equatorial_orientation(other.equatorial_orientation),
    parent_body(other.parent_body),
    meridian_angle(other.meridian_angle),
    epoch(other.epoch)
{
}

PT(RotationBase)
SynchronousRotation::make_copy(void) const
{
  return new SynchronousRotation(*this);
}

StellarAnchor*
SynchronousRotation::get_parent_body(void)
{
  return parent_body;
}

void
SynchronousRotation::set_parent_body(StellarAnchor *parent_body)
{
  this->parent_body = parent_body;
}

LQuaterniond
SynchronousRotation::get_frame_equatorial_orientation_at(double time)
{
  return equatorial_orientation;
}

LQuaterniond
SynchronousRotation::get_frame_rotation_at(double time)
{
  double angle = (time - epoch) * parent_body->get_orbit()->get_mean_motion() + meridian_angle;
  LQuaterniond rotation;
  rotation.set_from_axis_angle_rad(angle, LVector3d::unit_z());
  return rotation * get_frame_equatorial_orientation_at(time);
}

bool
SynchronousRotation::is_flipped(void) const
{
  return false;
}
