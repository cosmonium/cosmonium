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

#ifndef FRAMES_ANCHOR_H
#define FRAMES_ANCHOR_H

#include "frames_base.h"

class AnchorBase;

class AnchorReferenceFrame : public ReferenceFrame
{
PUBLISHED:
  AnchorReferenceFrame(AnchorBase *anchor = 0);

protected:
  AnchorReferenceFrame(AnchorReferenceFrame const &other);

PUBLISHED:
  PT(ReferenceFrame) make_copy(void) const;

  AnchorBase *get_anchor(void) const;
  void set_anchor(AnchorBase *anchor);
  MAKE_PROPERTY(anchor, get_anchor, set_anchor);

  virtual LPoint3d get_center(void);

  virtual LPoint3d get_absolute_reference_point(void);

  virtual LQuaterniond get_orientation(void);

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

  double get_right_ascension(void) const;
  void set_right_ascension(double ra);
  MAKE_PROPERTY(right_ascension, get_right_ascension, set_right_ascension);

  double get_declination(void) const;
  void set_declination(double decl);
  MAKE_PROPERTY(declination, get_declination, set_declination);

  double get_longitude_at_node(void) const;
  void set_longitude_at_node(double lon);
  MAKE_PROPERTY(longitude_at_node, get_longitude_at_node, set_longitude_at_node);

protected:
  double _right_ascension;
  double _declination;
  double _longitude_at_node;
  LQuaterniond orientation;

  MAKE_TYPE("CelestialReferenceFrame", AnchorReferenceFrame);
};

#endif
