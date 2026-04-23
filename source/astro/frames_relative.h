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

#ifndef FRAMES_RELATIVE_H
#define FRAMES_RELATIVE_H

#include "frames_base.h"

class RelativeReferenceFrame : public ReferenceFrame
{
PUBLISHED:
  RelativeReferenceFrame(ReferenceFrame *parent_frame, LPoint3d position, LQuaterniond orientation);

protected:
  RelativeReferenceFrame(RelativeReferenceFrame const &other);

PUBLISHED:
  PT(ReferenceFrame) make_copy(void) const;

  virtual LPoint3d get_center(void);

  virtual LQuaterniond get_orientation(void);

  virtual LPoint3d get_absolute_reference_point(void);

protected:
  PT(ReferenceFrame) parent_frame;
  LPoint3d frame_position;
  LQuaterniond frame_orientation;

  MAKE_TYPE("RelativeReferenceFrame", ReferenceFrame);
};

#endif
