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

#ifndef ORBITS_H
#define ORBITS_H

#include "referenceCount.h"
#include "pandabase.h"
#include "luse.h"
#include"type_utils.h"

#include "frames.h"

class OrbitBase : public TypedObject, public ReferenceCount
{
PUBLISHED:
  OrbitBase(ReferenceFrame *frame);

  virtual ~OrbitBase(void);

  virtual PT(OrbitBase) make_copy(void) const = 0;

  ReferenceFrame *get_frame(void);
  void set_frame(ReferenceFrame *frame);
  MAKE_PROPERTY(frame, get_frame, set_frame);

  virtual bool is_periodic(void) = 0;

  virtual bool is_closed(void) = 0;

  virtual bool is_dynamic(void) = 0;

  virtual double get_mean_motion(void) = 0;

  virtual LPoint3d get_absolute_reference_point_at(double time);

  virtual LPoint3d get_absolute_position_at(double time);

  virtual LPoint3d get_local_position_at(double time);

  virtual LPoint3d get_frame_position_at(double time) = 0;

  virtual LQuaterniond get_absolute_rotation_at(double time);

  virtual LQuaterniond get_frame_rotation_at(double time) = 0;

  virtual double get_bounding_radius(void);

  //Temporary until Python code is aligned
  double get_apparent_radius(void) { return get_bounding_radius(); }

  MAKE_TYPE_2("OrbitBase", TypedObject, ReferenceCount);

protected:
  PT(ReferenceFrame) frame;
};

class FixedPosition : public OrbitBase
{
PUBLISHED:
  FixedPosition(ReferenceFrame *frame);

protected:
  FixedPosition(FixedPosition const &other);

PUBLISHED:
  virtual bool is_periodic(void);

  virtual bool is_closed(void);

  virtual bool is_dynamic(void);

  virtual double get_mean_motion(void);

  MAKE_TYPE("FixedPosition", OrbitBase);
};

class AbsoluteFixedPosition : public FixedPosition
{
PUBLISHED:
  AbsoluteFixedPosition(ReferenceFrame *frame, LPoint3d absolute_reference_point);

protected:
  AbsoluteFixedPosition(AbsoluteFixedPosition const &other);

PUBLISHED:
  virtual PT(OrbitBase) make_copy(void) const;

  virtual LPoint3d get_absolute_reference_point_at(double time);

  virtual LPoint3d get_frame_position_at(double time);

  virtual LQuaterniond get_frame_rotation_at(double time);

  MAKE_TYPE("AbsoluteFixedPosition", FixedPosition);

protected:
  LPoint3d absolute_reference_point;
};

class LocalFixedPosition : public FixedPosition
{
PUBLISHED:
  LocalFixedPosition(ReferenceFrame *frame, LPoint3d frame_position);

protected:
  LocalFixedPosition(LocalFixedPosition const &other);

PUBLISHED:
  virtual PT(OrbitBase) make_copy(void) const;

  virtual LPoint3d get_frame_position_at(double time);

  virtual LQuaterniond get_frame_rotation_at(double time);

  MAKE_TYPE("LocalFixedPosition", FixedPosition);

protected:
  LPoint3d frame_position;
};

class EllipticalOrbit : public OrbitBase
{
PUBLISHED:
  EllipticalOrbit(ReferenceFrame *frame,
      double epoch,
      double mean_motion,
      double mean_anomaly,
      double pericenter_distance,
      double eccentricity,
      double argument_of_periapsis,
      double inclination,
      double ascending_node
      );

protected:
  EllipticalOrbit(EllipticalOrbit const &other);

PUBLISHED:
  virtual PT(OrbitBase) make_copy(void) const;

  virtual void update_rotation(void);

  virtual bool is_periodic(void);

  virtual bool is_closed(void);

  virtual bool is_dynamic(void);

  virtual double get_period(void);

  MAKE_PROPERTY(period, get_period);

  virtual double get_mean_motion(void);

  virtual LPoint3d get_frame_position_at(double time);

  virtual LQuaterniond get_frame_rotation_at(double time);

  virtual double get_bounding_radius(void);

  MAKE_TYPE("EllipticalOrbit", OrbitBase);

protected:
  double argument_of_periapsis;
  double inclination;
  double ascending_node;
  LQuaterniond rotation;

  double epoch;
  double mean_motion;
  double mean_anomaly;
  double pericenter_distance;
  double eccentricity;
};

class FunctionOrbit : public OrbitBase
{
PUBLISHED:
  FunctionOrbit(ReferenceFrame *frame,
      double average_period,
      double average_semi_major_axis,
      double average_eccentricity);

protected:
  FunctionOrbit(FunctionOrbit const &other);

PUBLISHED:
  virtual bool is_periodic(void);

  virtual bool is_closed(void);

  virtual bool is_dynamic(void);

  virtual double get_period(void);

  MAKE_PROPERTY(period, get_period);

  virtual double get_mean_motion(void);

  virtual double get_bounding_radius(void);

  MAKE_TYPE("FunctionOrbit", OrbitBase);

protected:
  double average_period;
  double bounding_radius;
};

#endif
