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

#ifndef CAMERA_HOLDER_H
#define CAMERA_HOLDER_H

#include "referenceCount.h"
#include "pandabase.h"
#include "nodePath.h"
#include "luse.h"
#include"type_utils.h"

class AnchorBase;
class CameraAnchor;
class PerspectiveLens;

class CameraHolder : public TypedObject, public ReferenceCount
{
PUBLISHED:
  CameraHolder(CameraAnchor *anchor, NodePath camera, PerspectiveLens *lens);
  virtual ~CameraHolder(void);

  CameraAnchor *get_anchor(void);
  void set_anchor(CameraAnchor *anchor);
  MAKE_PROPERTY(anchor, get_anchor, set_anchor);

  NodePath get_camera(void);
  void set_camera(NodePath camera);
  MAKE_PROPERTY(camera, get_camera, set_camera);

  double get_cos_fov2(void);
  void set_cos_fov2(double cos_fov2);
  MAKE_PROPERTY(cos_fov2, get_cos_fov2, set_cos_fov2);

  PerspectiveLens *get_lens(void);
  MAKE_PROPERTY(lens, get_lens);

protected:
  PT(CameraAnchor) anchor;
  NodePath camera;
  double cos_fov2;
  PT(PerspectiveLens) lens;

public:
  MAKE_TYPE_2("CameraHolder", TypedObject, ReferenceCount);
};

#endif
