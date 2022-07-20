/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2022 Laurent Deru.
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

#ifndef HALOPOINTSSETSHAPE_H
#define HALOPOINTSSETSHAPE_H

#include "pointsSetShape.h"


class HaloPointsSetShape : public PointsSetShape
{
PUBLISHED:
  HaloPointsSetShape(bool has_size, bool has_oid, double screen_scale);
  virtual ~HaloPointsSetShape(void);

  virtual void add_object(SceneAnchor *scene_anchor);

public:
  MAKE_TYPE("HaloPointsSetShape", PointsSetShape);
};

#endif
