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

#ifndef ROTATIONS_H
#define ROTATIONS_H

#include "referenceCount.h"
#include "pandabase.h"
#include "luse.h"
#include"type_utils.h"

class ReferenceFrame;
class StellarAnchor;

class RotationBase : public TypedObject, public ReferenceCount
{
PUBLISHED:
  RotationBase(ReferenceFrame *frame);

  virtual ~RotationBase(void);

  virtual PT(RotationBase) make_copy(void) const = 0;

  ReferenceFrame *get_frame(void);
  void set_frame(ReferenceFrame *frame);
  MAKE_PROPERTY(frame, get_frame, set_frame);

  virtual LQuaterniond get_equatorial_orientation_at(double time);

  virtual LQuaterniond get_frame_equatorial_orientation_at(double time) = 0;

  virtual LQuaterniond get_absolute_rotation_at(double time);

  virtual LQuaterniond get_frame_rotation_at(double time) = 0;

  virtual bool is_flipped(void) const;

public:
  LQuaterniond calc_orientation(double a, double d, bool flipped=false) const;

protected:
  PT(ReferenceFrame) frame;

  MAKE_TYPE_2("RotationBase", TypedObject, ReferenceCount);
};

class CachedRotationBase: public RotationBase
{
PUBLISHED:
  CachedRotationBase(ReferenceFrame *frame);
  virtual LQuaterniond get_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond get_frame_rotation_at(double time);

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time) = 0;
  virtual LQuaterniond calc_frame_rotation_at(double time) = 0;

private:
  double last_orientation_time;
  LQuaterniond last_orientation;
  double last_rotation_time;
  LQuaterniond last_rotation;

  MAKE_TYPE("CachedRotationBase", RotationBase);
};

class FixedRotation : public RotationBase
{
PUBLISHED:
  FixedRotation(LQuaterniond rotation, ReferenceFrame *frame);

protected:
  FixedRotation(FixedRotation const &other);

PUBLISHED:
  virtual PT(RotationBase) make_copy(void) const;

  virtual LQuaterniond get_frame_equatorial_orientation_at(double time);

  virtual LQuaterniond get_frame_rotation_at(double time);

protected:
  LQuaterniond rotation;

  MAKE_TYPE("FixedRotation", RotationBase);
};

class UnknownRotation : public RotationBase
{
PUBLISHED:
UnknownRotation(void);

protected:
  UnknownRotation(UnknownRotation const &other);

PUBLISHED:
  virtual PT(RotationBase) make_copy(void) const;

  virtual LQuaterniond get_frame_equatorial_orientation_at(double time);

  virtual LQuaterniond get_frame_rotation_at(double time);

  MAKE_TYPE("UnknownRotation", RotationBase);
};

class UniformRotation : public RotationBase
{
PUBLISHED:
  UniformRotation(LQuaterniond equatorial_orientation,
      double mean_motion,
      double meridian_angle,
      double epoch,
      ReferenceFrame *frame);

protected:
  UniformRotation(UniformRotation const &other);

PUBLISHED:
  virtual PT(RotationBase) make_copy(void) const;

  virtual LQuaterniond get_frame_equatorial_orientation_at(double time);

  virtual LQuaterniond get_frame_rotation_at(double time);

  virtual double get_period(void) const;

  virtual bool is_flipped(void) const;

  INLINE void set_period(double period);
  MAKE_PROPERTY(period, get_period, set_period);

  INLINE LQuaterniond get_equatorial_orientation(void);
  INLINE void set_equatorial_orientation(LQuaterniond equatorial_orientation);
  MAKE_PROPERTY(equatorial_orientation, get_equatorial_orientation, set_equatorial_orientation);

  INLINE double get_mean_motion(void);
  INLINE void set_mean_motion(double mean_motion);
  MAKE_PROPERTY(mean_motion, get_mean_motion, set_mean_motion);

  INLINE double get_meridian_angle(void);
  INLINE void set_meridian_angle(double meridian_angle);
  MAKE_PROPERTY(meridian_angle, get_meridian_angle, set_meridian_angle);

  INLINE double get_epoch(void);
  INLINE void set_epoch(double epoch);
  MAKE_PROPERTY(epoch, get_epoch, set_epoch);

protected:
  LQuaterniond equatorial_orientation;
  double mean_motion;
  double meridian_angle;
  double epoch;

  MAKE_TYPE("UniformRotation", RotationBase);
};

class SynchronousRotation : public RotationBase
{
PUBLISHED:
  SynchronousRotation(LQuaterniond equatorial_orientation,
      double meridian_angle,
      double epoch,
      ReferenceFrame *frame);

protected:
  SynchronousRotation(SynchronousRotation const &other);

PUBLISHED:
  virtual PT(RotationBase) make_copy(void) const;

  StellarAnchor *get_parent_body(void);
  void set_parent_body(StellarAnchor *parent_body);
  MAKE_PROPERTY(parent_body, get_parent_body, set_parent_body);

  virtual LQuaterniond get_frame_equatorial_orientation_at(double time);

  virtual LQuaterniond get_frame_rotation_at(double time);

  virtual bool is_flipped(void) const;

  INLINE LQuaterniond get_equatorial_orientation(void);
  INLINE void set_equatorial_orientation(LQuaterniond equatorial_orientation);
  MAKE_PROPERTY(equatorial_orientation, get_equatorial_orientation, set_equatorial_orientation);

  INLINE double get_meridian_angle(void);
  INLINE void set_meridian_angle(double meridian_angle);
  MAKE_PROPERTY(meridian_angle, get_meridian_angle, set_meridian_angle);

  INLINE double get_epoch(void);
  INLINE void set_epoch(double epoch);
  MAKE_PROPERTY(epoch, get_epoch, set_epoch);

protected:
  LQuaterniond equatorial_orientation;
  PT(StellarAnchor)  parent_body;
  double meridian_angle;
  double epoch;

  MAKE_TYPE("SynchronousRotation", RotationBase);
};

#include "rotations.I"

#endif
