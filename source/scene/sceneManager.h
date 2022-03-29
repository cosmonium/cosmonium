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

#ifndef SCENE_MANAGER_H
#define SCENE_MANAGER_H

#include "referenceCount.h"
#include "pandabase.h"
#include "nodePath.h"
#include "luse.h"
#include"type_utils.h"
#include "sceneAnchorCollection.h"


class SceneAnchor;
class CameraHolder;


class SceneManager : public TypedObject, public ReferenceCount
{
PUBLISHED:
  SceneManager(void);

  virtual ~SceneManager(void);

  virtual void set_target(GraphicsOutput *target) = 0;

  virtual void attach_new_anchor(NodePath instance) = 0;

  virtual void add_spread_object(NodePath instance) = 0;

  virtual void add_background_object(NodePath instance) = 0;

  virtual void init_camera(CameraHolder *camera_holder, NodePath default_camera) = 0;

  virtual void set_camera_mask(DrawMask flags) = 0;

  virtual void update_scene_and_camera(double distance_to_nearest, CameraHolder *camera_holder) = 0;

  virtual void build_scene(NodePath state, CameraHolder *camera_holder, SceneAnchorCollection visibles, SceneAnchorCollection resolved) = 0;

  virtual void ls(void) = 0;

  double get_scale(void);
  void set_scale(double scale);
  MAKE_PROPERTY(scale, get_scale, set_scale);

  double get_mid_plane(void);
  void set_mid_plane(double mid_plane);
  MAKE_PROPERTY(midPlane, get_mid_plane, set_mid_plane);

  static bool inverse_z;
  static double default_near_plane;
  static bool infinite_far_plane;
  static double default_far_plane;
  static double infinite_plane;
  static bool auto_infinite_plane;
  static double lens_far_limit;

protected:
  double scale;
  double mid_plane;

public:
  MAKE_TYPE_2("SceneManager", TypedObject, ReferenceCount);
};

#endif
