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

#include "orbits.h"
#include "kepler.h"
#include "astro.h"

TypeHandle OrbitBase::_type_handle;

OrbitBase::OrbitBase(ReferenceFrame *frame) :
  frame(frame)
{
}

OrbitBase::~OrbitBase(void)
{
}

ReferenceFrame *
OrbitBase::get_frame(void)
{
  return frame;
}

void
OrbitBase::set_frame(ReferenceFrame *frame)
{
  this->frame = frame;
}

LPoint3d
OrbitBase::get_absolute_reference_point_at(double time)
{
  return frame->get_absolute_reference_point();
}

LPoint3d
OrbitBase::get_absolute_position_at(double time)
{
  return frame->get_absolute_reference_point() + get_local_position_at(time);
}

LPoint3d
OrbitBase::get_local_position_at(double time)
{
  return frame->get_local_position(get_frame_rotation_at(time).xform(get_frame_position_at(time)));
}

LQuaterniond
OrbitBase::get_absolute_rotation_at(double time)
{
  return frame->get_absolute_orientation(get_frame_rotation_at(time));
}

double
OrbitBase::get_bounding_radius(void)
{
  return 0.0;
}

TypeHandle FixedPosition::_type_handle;

FixedPosition::FixedPosition(ReferenceFrame *frame) :
  OrbitBase(frame)
{
}

FixedPosition::FixedPosition(FixedPosition const &other) :
    OrbitBase(other.frame)
{
}

bool
FixedPosition::is_periodic(void)
{
  return false;
}

bool
FixedPosition::is_closed(void)
{
  return false;
}

bool
FixedPosition::is_dynamic(void)
{
  return false;
}

double
FixedPosition::get_mean_motion(void)
{
  return 0;
}

TypeHandle AbsoluteFixedPosition::_type_handle;

AbsoluteFixedPosition::AbsoluteFixedPosition(ReferenceFrame *frame, LPoint3d absolute_reference_point) :
  FixedPosition(frame),
  absolute_reference_point(absolute_reference_point)
{
}

AbsoluteFixedPosition::AbsoluteFixedPosition(AbsoluteFixedPosition const &other) :
    FixedPosition(other.frame),
    absolute_reference_point(other.absolute_reference_point)
{
}

PT(OrbitBase)
AbsoluteFixedPosition::make_copy(void) const
{
  return new AbsoluteFixedPosition(*this);
}

LPoint3d
AbsoluteFixedPosition::get_absolute_reference_point_at(double time)
{
  return absolute_reference_point;
}

LPoint3d
AbsoluteFixedPosition::get_frame_position_at(double time)
{
  return LPoint3d(0.0);
}

LQuaterniond
AbsoluteFixedPosition::get_frame_rotation_at(double time)
{
  return LQuaterniond::ident_quat();
}

TypeHandle LocalFixedPosition::_type_handle;

LocalFixedPosition::LocalFixedPosition(ReferenceFrame *frame, LPoint3d frame_position) :
  FixedPosition(frame),
  frame_position(frame_position)
{
}

LocalFixedPosition::LocalFixedPosition(LocalFixedPosition const &other) :
    FixedPosition(other.frame),
    frame_position(other.frame_position)
{
}

PT(OrbitBase)
LocalFixedPosition::make_copy(void) const
{
  return new LocalFixedPosition(*this);
}

LPoint3d
LocalFixedPosition::get_frame_position_at(double time)
{
  return frame_position;
}

LQuaterniond
LocalFixedPosition::get_frame_rotation_at(double time)
{
  return LQuaterniond::ident_quat();
}

TypeHandle EllipticalOrbit::_type_handle;

EllipticalOrbit::EllipticalOrbit(ReferenceFrame *frame,
    double epoch,
    double mean_motion,
    double mean_anomaly,
    double pericenter_distance,
    double eccentricity,
    double argument_of_periapsis,
    double inclination,
    double ascending_node
    ) :
        OrbitBase(frame),
        epoch(epoch),
        mean_motion(mean_motion),
        mean_anomaly(mean_anomaly),
        pericenter_distance(pericenter_distance),
        eccentricity(eccentricity),
        argument_of_periapsis(argument_of_periapsis),
        inclination(inclination),
        ascending_node(ascending_node)
{
  update_rotation();
}

EllipticalOrbit::EllipticalOrbit(EllipticalOrbit const &other) :
    OrbitBase(other.frame),
    epoch(other.epoch),
    mean_motion(other.mean_motion),
    mean_anomaly(other.mean_anomaly),
    pericenter_distance(other.pericenter_distance),
    eccentricity(other.eccentricity),
    argument_of_periapsis(other.argument_of_periapsis),
    inclination(other.inclination),
    ascending_node(other.ascending_node)
{
  update_rotation();
}

PT(OrbitBase)
EllipticalOrbit::make_copy(void) const
{
  return new EllipticalOrbit(*this);
}

void
EllipticalOrbit::update_rotation(void)
{
  LQuaterniond inclination_quat;
  inclination_quat.set_from_axis_angle_rad(inclination, LVector3d::unit_x());
  LQuaterniond arg_of_periapsis_quat;
  arg_of_periapsis_quat.set_from_axis_angle_rad(argument_of_periapsis, LVector3d::unit_z());
  LQuaterniond ascending_node_quat;
  ascending_node_quat.set_from_axis_angle_rad(ascending_node, LVector3d::unit_z());
  rotation = arg_of_periapsis_quat * inclination_quat * ascending_node_quat;
}

bool
EllipticalOrbit::is_periodic(void)
{
  return eccentricity < 1.0;
}

bool
EllipticalOrbit::is_closed(void)
{
  return eccentricity < 1.0;
}

bool
EllipticalOrbit::is_dynamic(void)
{
  return true;
}

double
EllipticalOrbit::get_mean_motion(void)
{
  return mean_motion;
}

LPoint3d
EllipticalOrbit::get_frame_position_at(double time)
{
  double current_mean_anomaly = (time - epoch) * mean_motion + mean_anomaly;
  return kepler_pos(pericenter_distance, eccentricity, current_mean_anomaly);
}

LQuaterniond
EllipticalOrbit::get_frame_rotation_at(double time)
{
  return rotation;
}

double
EllipticalOrbit::get_bounding_radius(void)
{
  return pericenter_distance * (1.0 + eccentricity) / (1.0 - eccentricity);
}

TypeHandle FunctionOrbit::_type_handle;

FunctionOrbit::FunctionOrbit(ReferenceFrame *frame,
    double average_period,
    double average_semi_major_axis,
    double average_eccentricity) :
  OrbitBase(frame),
  average_period(average_period)
{
  //TODO: We should add a margin, or use max semi-major axis and eccentricity
  bounding_radius = average_semi_major_axis * (1.0 + average_eccentricity);
}

FunctionOrbit::FunctionOrbit(FunctionOrbit const &other) :
  OrbitBase(other.frame),
  average_period(other.average_period),
  bounding_radius(other.bounding_radius)
{
}

bool
FunctionOrbit::is_periodic(void)
{
  return true;
}

bool
FunctionOrbit::is_closed(void)
{
  return true;
}

bool
FunctionOrbit::is_dynamic(void)
{
  return true;
}

double
FunctionOrbit::get_period(void)
{
  return average_period;
}

double
FunctionOrbit::get_mean_motion(void)
{
  return 2 * M_PI / average_period;
}

double
FunctionOrbit::get_bounding_radius(void)
{
  return bounding_radius;
}
