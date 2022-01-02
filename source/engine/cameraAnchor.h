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

#ifndef CAMERAANCHOR_H
#define CAMERAANCHOR_H

#include "cartesianAnchor.h"

class InfiniteFrustum;

class CameraAnchor : public CartesianAnchor
{
PUBLISHED:
  CameraAnchor(PyObject *ref_object, ReferenceFrame *frame);
  virtual ~CameraAnchor(void);

  virtual void do_update(void);

  InfiniteFrustum *get_frustum(void);
  void set_frustum(InfiniteFrustum *frustum);
  MAKE_PROPERTY(frustum, get_frustum, set_frustum);

  InfiniteFrustum *get_relative_frustum(void);
  void set_relative_frustum(InfiniteFrustum *frustum);
  MAKE_PROPERTY(rel_frustum, get_relative_frustum, set_relative_frustum);

PUBLISHED:
  double pixel_size;
  LVector3d camera_vector;

public:
  PT(InfiniteFrustum) frustum;
  PT(InfiniteFrustum) rel_frustum;

  MAKE_TYPE("CameraAnchor", CartesianAnchor);
};

#endif
