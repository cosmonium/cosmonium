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

#ifndef SCENE_REGION_H
#define SCENE_REGION_H

#include "referenceCount.h"
#include "pandabase.h"
#include "nodePath.h"
#include "luse.h"
#include"type_utils.h"

class AnchorBase;
class Camera;
class CameraHolder;
class DisplayRegion;
class GrahicsOoutput;
class RenderState;
class SceneAnchor;
class SceneManager;

class SceneRegion : public TypedObject, public ReferenceCount
{
PUBLISHED:
  SceneRegion(SceneManager *scene_manager, double near, double far);
  virtual ~SceneRegion(void);

  void set_camera_mask(DrawMask flags);

  void add_body(SceneAnchor *body);

  void add_point(SceneAnchor *point);

  bool overlap(SceneRegion *other);

  void merge(SceneRegion *other);

  void create(GraphicsOutput *target,
      const RenderState *state,
      CameraHolder *camera_holder,
      DrawMask camera_mask,
      bool inverse_z,
      double section_near,
      double section_far,
      int sort_index);

  void remove(void);

  void ls(void);

  int get_num_points(void) const;
  SceneAnchor *get_point(int index) const;
  MAKE_SEQ(get_points, get_num_points, get_point);

  double get_near(void) const;
  double get_far(void) const;
  NodePath get_root(void) const;

public:
  std::vector<PT(SceneAnchor)> const & get_points(void) const;

protected:
  PT(SceneManager) scene_manager;
  std::vector<PT(SceneAnchor)> bodies;
  std::vector<PT(SceneAnchor)> points;
  double near;
  double far;
  PT(GraphicsOutput) target;
  PT(DisplayRegion) region;
  NodePath root;
  PT(Camera) cam;
  NodePath cam_np;

public:
  MAKE_TYPE_2("SceneRegion", TypedObject, ReferenceCount);
};

#endif
