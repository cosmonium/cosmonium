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

#ifndef SCENE_ANCHOR_H
#define SCENE_ANCHOR_H

#include "referenceCount.h"
#include "pandabase.h"
#include "nodePath.h"
#include "luse.h"
#include"type_utils.h"

class AnchorBase;
class SceneManager;

class SceneAnchor : public TypedObject, public ReferenceCount
{
PUBLISHED:
  SceneAnchor(AnchorBase *anchor,
      bool support_offset_body_center,
      bool apply_orientation=false,
      bool background=false,
      bool virtual_object=false);
  virtual ~SceneAnchor(void);

  void create_instance(SceneManager *scene_manager);
  void remove_instance(void);
  void update(SceneManager *scene_manager);

  void calc_scene_params(SceneManager *scene_manager, LVector3d rel_position, LPoint3d abs_position, double distance_to_obs, LVector3d vector_to_obs,
      LPoint3d &position, double &distance, double &scale_factor);

  AnchorBase *get_anchor(void);
  MAKE_PROPERTY(anchor, get_anchor);

  bool get_background(void);
  void set_background(bool background);
  MAKE_PROPERTY(background, get_background, get_background);

  NodePath *get_instance(void);
  MAKE_PROPERTY(instance, get_instance);

  NodePath *get_unshifted_instance(void);
  MAKE_PROPERTY(unshifted_instance, get_unshifted_instance);

  NodePath *get_shifted_instance(void);
  MAKE_PROPERTY(shifted_instance, get_shifted_instance);

  bool get_virtual_object(void);
  void set_virtual_object(bool get_virtual_object);
  MAKE_PROPERTY(virtual_object, get_virtual_object, set_virtual_object);

  static bool offset_body_center;
  static bool camera_at_origin;
  static bool use_depth_scaling;
  static bool use_inv_scaling;
  static bool use_log_scaling;

protected:
  AnchorBase *anchor;
  bool background;
  bool support_offset_body_center;
  bool apply_orientation;
  bool has_instance;
  NodePath instance;
  NodePath shifted_instance;
  NodePath unshifted_instance;
  bool virtual_object;

PUBLISHED:
  LPoint3d scene_position;
  LQuaternion scene_orientation;
  double scene_scale_factor;
  LPoint3d scene_rel_position;
  LVector3d world_body_center_offset;
  LVector3d scene_body_center_offset;

public:
  MAKE_TYPE_2("SceneAnchor", TypedObject, ReferenceCount);
};

#endif
