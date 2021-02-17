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

#ifndef OBSERVER_H
#define OBSERVER_H

#include "pandabase.h"
#include "luse.h"

class InfiniteFrustum;

class Observer
{
PUBLISHED:
  virtual ~Observer(void);

  virtual LPoint3d get_absolute_reference_point(void);

  virtual LPoint3d get_absolute_position(void);

  virtual LPoint3d get_local_position(void);

  virtual LQuaterniond get_absolute_orientation(void);

  virtual void update(LPoint3d absolute_reference_point, LPoint3d local_position, LQuaterniond orientation);

PUBLISHED:
  double pixel_size;
  InfiniteFrustum *frustum;
  InfiniteFrustum *rel_frustum;
  double midPlane;

protected:
  //Cached values
  LPoint3d _absolute_reference_point;
  LPoint3d _local_position;
  LQuaterniond _orientation;
};

#endif
