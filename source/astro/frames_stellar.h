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

#ifndef FRAMES_STELLAR_H
#define FRAMES_STELLAR_H

#include "frames_base.h"

class StellarAnchor;

class StellarAnchorReferenceFrame : public ReferenceFrame
{
PUBLISHED:
  StellarAnchorReferenceFrame(StellarAnchor *anchor = 0);

protected:
  StellarAnchorReferenceFrame(StellarAnchorReferenceFrame const &other);

PUBLISHED:
  PT(ReferenceFrame) make_copy(void) const;

  StellarAnchor *get_anchor(void);
  void set_anchor(StellarAnchor *anchor);
  MAKE_PROPERTY(anchor, get_anchor, set_anchor);

  virtual LPoint3d get_center(void);

  virtual LPoint3d get_absolute_reference_point(void);

  virtual LQuaterniond get_orientation(void);

protected:
  PT(StellarAnchor) anchor;

  MAKE_TYPE("StellarAnchorReferenceFrame", ReferenceFrame);
};

class OrbitReferenceFrame : public StellarAnchorReferenceFrame
{
PUBLISHED:
  OrbitReferenceFrame(StellarAnchor *anchor = 0);

protected:
  OrbitReferenceFrame(OrbitReferenceFrame const &other);

PUBLISHED:
  PT(ReferenceFrame) make_copy(void) const;

  virtual LQuaterniond get_orientation(void);

  MAKE_TYPE("OrbitReferenceFrame", StellarAnchorReferenceFrame);
};

class EquatorialReferenceFrame : public StellarAnchorReferenceFrame
{
PUBLISHED:
  EquatorialReferenceFrame(StellarAnchor *anchor = 0);

protected:
  EquatorialReferenceFrame(EquatorialReferenceFrame const &other);

PUBLISHED:
  PT(ReferenceFrame) make_copy(void) const;

  virtual LQuaterniond get_orientation(void);

  MAKE_TYPE("EquatorialReferenceFrame", StellarAnchorReferenceFrame);
};

class SynchroneReferenceFrame : public StellarAnchorReferenceFrame
{
PUBLISHED:
  SynchroneReferenceFrame(StellarAnchor *anchor = 0);

protected:
  SynchroneReferenceFrame(SynchroneReferenceFrame const &other);

PUBLISHED:
  PT(ReferenceFrame) make_copy(void) const;

  virtual LQuaterniond get_orientation(void);

  MAKE_TYPE("SynchroneReferenceFrame", StellarAnchorReferenceFrame);
};

#endif
