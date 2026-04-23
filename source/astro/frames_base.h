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

#ifndef FRAMES_BASE_H
#define FRAMES_BASE_H

#include "referenceCount.h"
#include "pandabase.h"
#include "luse.h"
#include "type_utils.h"

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

// TODO: This should be an actual class and J2000BarycentricEclipticReferenceFrame derives from it
#define AbsoluteReferenceFrame J2000BarycentricEclipticReferenceFrame

#endif
