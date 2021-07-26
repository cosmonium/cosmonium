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

#ifndef FRAMES_H
#define FRAMES_H

#include "referenceCount.h"
#include "pandabase.h"
#include "luse.h"
#include"type_utils.h"

class AnchorBase;

class ReferenceFrame : public TypedObject, public ReferenceCount
{
PUBLISHED:
  virtual ~ReferenceFrame(void);

  virtual PT(ReferenceFrame) make_copy(void) const = 0;

  virtual LPoint3d get_center(void) = 0;

  virtual LQuaterniond get_orientation(void) = 0;

  virtual LPoint3d get_absolute_reference_point(void) = 0;

  virtual LPoint3d get_absolute_position(LPoint3d frame_position);

  virtual LPoint3d get_local_position(LPoint3d frame_position);

  virtual LPoint3d get_frame_position(LPoint3d local_position);

  virtual LQuaterniond get_absolute_orientation(LQuaterniond frame_orientation);

  virtual LQuaterniond get_frame_orientation(LQuaterniond absolute_orientation);

  MAKE_TYPE_2("ReferenceFrame", TypedObject, ReferenceCount);
};

class J2000BarycentricEclipticReferenceFrame : public ReferenceFrame
{
PUBLISHED:
  J2000BarycentricEclipticReferenceFrame(void);

protected:
  J2000BarycentricEclipticReferenceFrame(J2000BarycentricEclipticReferenceFrame const &other);

PUBLISHED:
  PT(ReferenceFrame) make_copy(void) const;

  virtual LPoint3d get_center(void);

  virtual LQuaterniond get_orientation(void);

  virtual LPoint3d get_absolute_reference_point(void);

  MAKE_TYPE("J2000BarycentricEclipticReferenceFrame", ReferenceFrame);
};

class J2000BarycentricEquatorialReferenceFrame : public ReferenceFrame
{
PUBLISHED:
  J2000BarycentricEquatorialReferenceFrame(void);

protected:
  J2000BarycentricEquatorialReferenceFrame(J2000BarycentricEquatorialReferenceFrame const &other);

PUBLISHED:
  PT(ReferenceFrame) make_copy(void) const;

  virtual LPoint3d get_center(void);

  virtual LQuaterniond get_orientation(void);

  virtual LPoint3d get_absolute_reference_point(void);

  MAKE_TYPE("J2000BarycentricEquatorialReferenceFrame", ReferenceFrame);
};

class AnchorReferenceFrame : public ReferenceFrame
{
PUBLISHED:
  AnchorReferenceFrame(AnchorBase *anchor = 0);

protected:
  AnchorReferenceFrame(AnchorReferenceFrame const &other);

PUBLISHED:
  AnchorBase *get_anchor(void);
  void set_anchor(AnchorBase *anchor);
  MAKE_PROPERTY(anchor, get_anchor, set_anchor);

  virtual LPoint3d get_center(void);

  virtual LPoint3d get_absolute_reference_point(void);

protected:
  PT(AnchorBase) anchor;

  MAKE_TYPE("AnchorReferenceFrame", ReferenceFrame);
};

class J2000EclipticReferenceFrame : public AnchorReferenceFrame
{
PUBLISHED:
  J2000EclipticReferenceFrame(AnchorBase *anchor = 0);

protected:
  J2000EclipticReferenceFrame(J2000EclipticReferenceFrame const &other);

PUBLISHED:
  PT(ReferenceFrame) make_copy(void) const;

  virtual LQuaterniond get_orientation(void);

  MAKE_TYPE("J2000EclipticReferenceFrame", AnchorReferenceFrame);
};

class J2000EquatorialReferenceFrame : public AnchorReferenceFrame
{
PUBLISHED:
  J2000EquatorialReferenceFrame(AnchorBase *anchor = 0);

protected:
  J2000EquatorialReferenceFrame(J2000EquatorialReferenceFrame const &other);

PUBLISHED:
  PT(ReferenceFrame) make_copy(void) const;

  virtual LQuaterniond get_orientation(void);

  MAKE_TYPE("J2000EquatorialReferenceFrame", AnchorReferenceFrame);
};

class CelestialReferenceFrame : public AnchorReferenceFrame
{
PUBLISHED:
  CelestialReferenceFrame(AnchorBase *anchor = 0,
      double right_ascension=0.0,
      double declination=0.0,
      double longitude_at_node=0.0);

protected:
  CelestialReferenceFrame(CelestialReferenceFrame const &other);

PUBLISHED:
  PT(ReferenceFrame) make_copy(void) const;

  void update_orientation(void);

  virtual LQuaterniond get_orientation(void);

public:
  double right_ascension;
  double declination;
  double longitude_at_node;

protected:
  LQuaterniond orientation;

  MAKE_TYPE("CelestialReferenceFrame", AnchorReferenceFrame);
};

class OrbitReferenceFrame : public AnchorReferenceFrame
{
PUBLISHED:
  OrbitReferenceFrame(AnchorBase *anchor = 0);

protected:
  OrbitReferenceFrame(OrbitReferenceFrame const &other);

PUBLISHED:
  PT(ReferenceFrame) make_copy(void) const;

  virtual LQuaterniond get_orientation(void);

  MAKE_TYPE("OrbitReferenceFrame", AnchorReferenceFrame);
};

class EquatorialReferenceFrame : public AnchorReferenceFrame
{
PUBLISHED:
  EquatorialReferenceFrame(AnchorBase *anchor = 0);

protected:
  EquatorialReferenceFrame(EquatorialReferenceFrame const &other);

PUBLISHED:
  PT(ReferenceFrame) make_copy(void) const;

  virtual LQuaterniond get_orientation(void);

  MAKE_TYPE("EquatorialReferenceFrame", AnchorReferenceFrame);
};

class SynchroneReferenceFrame : public AnchorReferenceFrame
{
PUBLISHED:
  SynchroneReferenceFrame(AnchorBase *anchor = 0);

protected:
  SynchroneReferenceFrame(SynchroneReferenceFrame const &other);

PUBLISHED:
  PT(ReferenceFrame) make_copy(void) const;

  virtual LQuaterniond get_orientation(void);

  MAKE_TYPE("SynchroneReferenceFrame", AnchorReferenceFrame);
};

class RelativeReferenceFrame : public AnchorReferenceFrame
{
PUBLISHED:
  RelativeReferenceFrame(ReferenceFrame *parent_frame, AnchorBase *anchor = 0);

protected:
  RelativeReferenceFrame(RelativeReferenceFrame const &other);

PUBLISHED:
  PT(ReferenceFrame) make_copy(void) const;

  virtual LQuaterniond get_orientation(void);

protected:
  PT(ReferenceFrame) parent_frame;

  MAKE_TYPE("RelativeReferenceFrame", AnchorReferenceFrame);
};

#endif
