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

#ifndef STATIC_SCENE_MANAGER_H
#define STATIC_SCENE_MANAGER_H

#include"sceneManager.h"

class DisplayRegion;
class PerspectiveLens;

class StaticSceneManager : public SceneManager
{
PUBLISHED:
  StaticSceneManager(NodePath render);
  virtual ~StaticSceneManager(void);

  virtual void set_target(GraphicsOutput *target);

  virtual void attach_new_anchor(NodePath instance);

  virtual void add_spread_object(NodePath instance);

  virtual void add_background_object(NodePath instance);

  virtual void init_camera(CameraHolder *camera_holder, NodePath default_camera);

  virtual void set_camera_mask(DrawMask flags);

  virtual void update_scene_and_camera(double distance_to_nearest, CameraHolder *camera_holder);

  virtual void build_scene(NodePath state, CameraHolder *camera_holder, SceneAnchorCollection visibles, SceneAnchorCollection resolved);

  virtual void ls(void);

  virtual double get_infinity(void) const;

  NodePath get_camera(void);
  MAKE_PROPERTY(camera, get_camera);

  NodePath get_root(void);
  MAKE_PROPERTY(root, get_root);

protected:
  NodePath camera;
  PT(PerspectiveLens) lens;
  PT(DisplayRegion) dr;
  double near_plane;
  double far_plane;
  double infinity;
  NodePath root;

public:
  MAKE_TYPE("StaticSceneManager", SceneManager);
};

#endif
