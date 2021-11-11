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

#include "observer.h"

Observer::~Observer(void)
{
}

LPoint3d
Observer::get_absolute_reference_point(void)
{
  return _absolute_reference_point;
}

LPoint3d
Observer::get_absolute_position(void)
{
  return _absolute_reference_point + _local_position;
}

LPoint3d
Observer::get_local_position(void)
{
  return _local_position;
}

LQuaterniond
Observer::get_absolute_orientation(void)
{
  return _orientation;
}

void
Observer::update(LPoint3d absolute_reference_point, LPoint3d local_position, LQuaterniond orientation, LVector3d camera_vector)
{
  _absolute_reference_point = absolute_reference_point;
  _local_position = local_position;
  _orientation = orientation;
  this->camera_vector = camera_vector;
}
