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

#ifndef REGION_SCENE_MANAGER_H
#define REGION_SCENE_MANAGER_H

#include"sceneManager.h"

class DisplayRegion;
class PerspectiveLens;
class SceneRegion;

class RegionSceneManager : public SceneManager
{
PUBLISHED:
RegionSceneManager(void);
  virtual ~RegionSceneManager(void);

  virtual void set_target(GraphicsOutput *target);

  virtual void attach_new_anchor(NodePath instance);

  virtual void add_spread_object(NodePath instance);

  void attach_spread_objects(void);

  virtual void add_background_object(NodePath instance);

  virtual void init_camera(CameraHolder *camera_holder, NodePath default_camera);

  virtual void set_camera_mask(DrawMask flags);

  virtual void update_scene_and_camera(double distance_to_nearest, CameraHolder *camera_holder);

  void clear_scene(void);

  virtual void build_scene(NodePath state, CameraHolder *camera_holder, SceneAnchorCollection visibles, SceneAnchorCollection resolved);

  virtual void ls(void);

  static double min_near;
  static double max_near_reagion;
  static double infinity;
  static bool render_sprite_points;

protected:
  PT(GraphicsOutput) target;
  std::list<PT(SceneRegion)> regions;
  std::vector<NodePath> spread_objects;
  PT(SceneRegion) background_region;
  DrawMask camera_mask;

public:
  MAKE_TYPE("RegionSceneManager", SceneManager);
};

#endif
