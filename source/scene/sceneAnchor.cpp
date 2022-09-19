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


#include "anchor.h"
#include "sceneAnchor.h"
#include "sceneManager.h"

TypeHandle SceneAnchor::_type_handle;

bool SceneAnchor::offset_body_center = true;
bool SceneAnchor::camera_at_origin = true;
bool SceneAnchor::use_depth_scaling = false;
bool SceneAnchor::use_inv_scaling = true;
bool SceneAnchor::use_log_scaling = false;

SceneAnchor::SceneAnchor(AnchorBase *anchor,
    bool support_offset_body_center,
    LColor oid_color,
    bool apply_orientation,
    bool background,
    bool virtual_object,
    bool spread_object) :
    anchor(anchor),
    background(background),
    support_offset_body_center(support_offset_body_center),
    apply_orientation(apply_orientation),
    has_instance(false),
    virtual_object(virtual_object),
    spread_object(spread_object),
    scene_position(0),
    scene_orientation(0),
    scene_scale_factor(0),
    scene_rel_position(0),
    world_body_center_offset(0),
    scene_body_center_offset(0),
    oid_color(oid_color)
{
}

SceneAnchor::~SceneAnchor(void)
{
}

void
SceneAnchor::create_instance(SceneManager *scene_manager)
{
  if (!has_instance) {
    instance = NodePath("scene-anchor");
    scene_manager->attach_new_anchor(instance);
    shifted_instance = instance.attach_new_node("shifted-anchor");
    unshifted_instance = instance.attach_new_node("unshifted-anchor");
    has_instance = true;
  }
}

void
SceneAnchor::remove_instance(void)
{
  if (has_instance) {
    instance.remove_node();
    shifted_instance.remove_node();
    unshifted_instance.remove_node();
    has_instance = false;
  }
}

void
SceneAnchor::update(SceneManager *scene_manager)
{
  double distance_to_obs;
  double scene_distance;
  if (support_offset_body_center && anchor->visible && anchor->resolved && offset_body_center) {
      world_body_center_offset = -anchor->vector_to_obs * anchor->_height_under * scene_scale_factor;
      scene_body_center_offset = -anchor->vector_to_obs * anchor->_height_under;
      scene_rel_position = anchor->rel_position - scene_body_center_offset;
      distance_to_obs = anchor->distance_to_obs - anchor->_height_under;
      calc_scene_params(scene_manager, scene_rel_position, anchor->_position, distance_to_obs, anchor->vector_to_obs,
          scene_position, scene_distance, scene_scale_factor);
      if (has_instance) {
          unshifted_instance.set_pos(LCAST(PN_stdfloat, scene_body_center_offset));
      }
  } else {
      scene_rel_position = anchor->rel_position;
      distance_to_obs = anchor->distance_to_obs;
      calc_scene_params(scene_manager, scene_rel_position, anchor->_position, distance_to_obs, anchor->vector_to_obs,
          scene_position, scene_distance, scene_scale_factor);
      if (has_instance) {
          unshifted_instance.set_pos(LPoint3(0));
      }
  }
  if (has_instance) {
      instance.set_pos(LCAST(PN_stdfloat, scene_position));
      if (apply_orientation) {
          scene_orientation = LQuaternion(LCAST(PN_stdfloat, anchor->_orientation));
          instance.set_quat(scene_orientation);
      }
      instance.set_scale(scene_scale_factor);
  }
}

void
SceneAnchor::calc_scene_params(SceneManager *scene_manager, LVector3d rel_position, LPoint3d abs_position, double distance_to_obs, LVector3d vector_to_obs,
    LPoint3d &position, double &distance, double &scale_factor)
{
  LPoint3d obj_position;

  if (camera_at_origin) {
      obj_position = rel_position;
  } else {
      obj_position = abs_position;
  }
  double midPlane = scene_manager->get_mid_plane();
  double scale = scene_manager->get_scale();
  distance_to_obs /= scale;
  if (!use_depth_scaling || distance_to_obs <= midPlane) {
      position = obj_position / scale;
      distance = distance_to_obs;
      scale_factor = 1.0 / scale;
  } else if (use_inv_scaling) {
      LPoint3d not_scaled = -vector_to_obs * midPlane;
      double scaled_distance = midPlane * (1 - midPlane / distance_to_obs);
      LPoint3d scaled = -vector_to_obs * scaled_distance;
      position = not_scaled + scaled;
      distance = midPlane + scaled_distance;
      double ratio = distance / distance_to_obs;
      scale_factor = ratio / scale;
  } else if (use_log_scaling) {
      LPoint3d not_scaled = -vector_to_obs * midPlane;
      double scaled_distance = midPlane * (1 - log2(midPlane / distance_to_obs + 1));
      LPoint3d scaled = -vector_to_obs * scaled_distance;
      position = not_scaled + scaled;
      distance = midPlane + scaled_distance;
      double ratio = distance / distance_to_obs;
      scale_factor = ratio / scale;
  }
}


LPoint3d
SceneAnchor::calc_scene_position(SceneManager *scene_manager, LVector3d rel_position, LPoint3d abs_position, double distance_to_obs, LVector3d vector_to_obs)
{
  LPoint3d scene_position;
  LPoint3d obj_position;

  if (camera_at_origin) {
      obj_position = rel_position;
  } else {
      obj_position = abs_position;
  }
  double midPlane = scene_manager->get_mid_plane();
  double scale = scene_manager->get_scale();
  distance_to_obs /= scale;
  if (!use_depth_scaling || distance_to_obs <= midPlane) {
      scene_position = obj_position / scale;
  } else if (use_inv_scaling) {
      LPoint3d not_scaled = -vector_to_obs * midPlane;
      double scaled_distance = midPlane * (1 - midPlane / distance_to_obs);
      LPoint3d scaled = -vector_to_obs * scaled_distance;
      scene_position = not_scaled + scaled;
  } else if (use_log_scaling) {
      LPoint3d not_scaled = -vector_to_obs * midPlane;
      double scaled_distance = midPlane * (1 - log2(midPlane / distance_to_obs + 1));
      LPoint3d scaled = -vector_to_obs * scaled_distance;
      scene_position = not_scaled + scaled;
  }
  return scene_position;
}


AnchorBase *
SceneAnchor::get_anchor(void)
{
    return anchor;
}


bool
SceneAnchor::get_background(void)
{
    return background;
}


void
SceneAnchor::set_background(bool background)
{
    this->background = background;
}


NodePath *
SceneAnchor::get_instance(void)
{
  if (has_instance) {
    return &instance;
  } else {
    return nullptr;
  }
}


NodePath *
SceneAnchor::get_unshifted_instance(void)
{
  if (has_instance) {
    return &unshifted_instance;
  } else {
    return nullptr;
  }
}


NodePath *
SceneAnchor::get_shifted_instance(void)
{
  if (has_instance) {
    return &shifted_instance;
  } else {
    return nullptr;
  }
}


LColor
SceneAnchor::get_oid_color(void)
{
    return background;
}


void
SceneAnchor::set_oid_color(LColor oid_color)
{
    this->oid_color = oid_color;
}


bool
SceneAnchor::get_virtual_object(void)
{
    return virtual_object;
}


void
SceneAnchor::set_virtual_object(bool virtual_object)
{
    this->virtual_object = virtual_object;
}


bool
SceneAnchor::get_spread_object(void)
{
    return spread_object;
}


void
SceneAnchor::set_spread_object(bool spread_object)
{
    this->spread_object = spread_object;
}


TypeHandle AbsoluteSceneAnchor::_type_handle;


AbsoluteSceneAnchor::AbsoluteSceneAnchor(AnchorBase *anchor) :
    SceneAnchor(anchor, false, LColor())
{
}


void
AbsoluteSceneAnchor::update(SceneManager *scene_manager)
{
  if (camera_at_origin) {
      scene_position = anchor->rel_position / scene_manager->get_scale();
      instance.set_pos(LCAST(PN_stdfloat, scene_position));
      scene_scale_factor = 1.0 / scene_manager->get_scale();
      instance.set_scale(scene_scale_factor);
  }
}


TypeHandle ObserverSceneAnchor::_type_handle;


ObserverSceneAnchor::ObserverSceneAnchor(AnchorBase *anchor, bool background) :
    SceneAnchor(anchor, false, LColor(), false, background)
{
}


void
ObserverSceneAnchor::update(SceneManager *scene_manager)
{
  if (!camera_at_origin) {
      scene_position = anchor->rel_position / scene_manager->get_scale();
      instance.set_pos(LCAST(PN_stdfloat, scene_position));
      scene_scale_factor = 1.0 / scene_manager->get_scale();
      instance.set_scale(scene_scale_factor);
  }
}
