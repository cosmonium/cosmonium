/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2019 Laurent Deru.
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

#include "octreeLeaf.h"
#include "py_panda.h"

OctreeLeaf::OctreeLeaf(PyObject *ref_object, LPoint3d position, double abs_magnitude, double extend, LColor point_color) :
  ref_object(ref_object),
  position(position),
  abs_magnitude(abs_magnitude),
  extend(extend),
  point_color(point_color),
  update_id(0)
{
  Py_INCREF(ref_object);
}

OctreeLeaf::~OctreeLeaf(void)
{
  Py_DECREF(ref_object);
}

PyObject *
OctreeLeaf::get_object(void) const
{
  Py_INCREF(ref_object);
  return ref_object;
}

void
OctreeLeaf::update_pos_and_visibility(LPoint3d camera_global_pos, LPoint3d camera_position, double pixel_size, double min_body_size)
{
  LVector3d global_delta = get_global_position() - camera_global_pos;
  LVector3d local_delta = -camera_position; //No local position for leaves in the octree
  rel_position = global_delta + local_delta;
  distance_to_obs = rel_position.length();
  vector_to_obs = -rel_position / distance_to_obs;
  if (distance_to_obs > 0.0) {
      visible_size = get_extend() / (distance_to_obs * pixel_size);
      resolved = visible_size > min_body_size;
  } else {
    visible_size = 0.0;
    resolved = true;
  }
  visible = true; //If we are here, it's because the leaf is below limit magnitude
}

bool use_depth_scaling = true;
bool use_inv_scaling = true;
bool use_log_scaling = false;

void
OctreeLeaf::update_scene_info(double midPlane, double scale)
{
  double reduced_distance_to_obs = distance_to_obs / scale;
  if (!use_depth_scaling || reduced_distance_to_obs <= midPlane) {
    scene_position = rel_position / scale;
    scene_distance = reduced_distance_to_obs;
    scene_scale_factor = 1.0 / scale;
  } else if (use_inv_scaling) {
    LVector3d not_scaled = -vector_to_obs * midPlane;
    double scaled_distance = midPlane * (1 - midPlane / reduced_distance_to_obs);
    LVector3d scaled = -vector_to_obs * scaled_distance;
    scene_position = not_scaled + scaled;
    scene_distance = midPlane + scaled_distance;
    double ratio = scene_distance / reduced_distance_to_obs;
    scene_scale_factor = ratio / scale;
  } else if (use_log_scaling) {
    LVector3d not_scaled = -vector_to_obs * midPlane;
    double scaled_distance = midPlane;// * (1 - log(midPlane / reduced_distance_to_obs + 1, 2));
    LVector3d scaled = -vector_to_obs * scaled_distance;
    scene_position = not_scaled + scaled;
    scene_distance = midPlane + scaled_distance;
    double ratio = scene_distance / reduced_distance_to_obs;
    scene_scale_factor = ratio / scale;
  }
  scene_orientation = LQuaterniond();
}
