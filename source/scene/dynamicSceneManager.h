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

#ifndef DYNAMIC_SCENE_MANAGER_H
#define DYNAMIC_SCENE_MANAGER_H

#include"sceneManager.h"

class DisplayRegion;
class CollisionHandlerQueue;
class PerspectiveLens;
class RenderPass;


class DynamicSceneManager : public SceneManager
{
PUBLISHED:
  DynamicSceneManager(NodePath render);
  virtual ~DynamicSceneManager(void);

  virtual bool has_regions(void) const;

  virtual void add_pass(const std::string &name, GraphicsOutput *target, DrawMask camera_mask);

  virtual void attach_new_anchor(NodePath instance);

  virtual void add_spread_object(NodePath instance);

  virtual void add_background_object(NodePath instance);

  void update_planes(void);

  virtual void init_camera(CameraHolder *camera_holder, NodePath default_camera);

  virtual void update_scene_and_camera(double distance_to_nearest, CameraHolder *camera_holder);

  virtual void build_scene(NodePath state, CameraHolder *camera_holder, SceneAnchorCollection visibles, SceneAnchorCollection resolved);

  PT(CollisionHandlerQueue) pick_scene(LPoint2 mpos);

  virtual void ls(void);

  NodePath get_camera(void);
  MAKE_PROPERTY(camera, get_camera);

  virtual double get_infinity(void) const;

  NodePath get_root(void);
  MAKE_PROPERTY(root, get_root);


  static bool auto_scale;
  static double min_scale;
  static double max_scale;
  static bool set_frustum;
  static double mid_plane_ratio;

protected:
  std::vector<PT(RenderPass)> rendering_passes;
  PT(PerspectiveLens) lens;
  double near_plane;
  double far_plane;
  double infinity;
  NodePath root;

public:
  MAKE_TYPE("DynamicSceneManager", SceneManager);
};

#endif
