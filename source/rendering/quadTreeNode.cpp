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

#include "py_panda.h"
#include "dcast.h"
#include "cullingFrustum.h"
#include "lodControl.h"
#include "lodResult.h"
#include "quadTreeNodeCollection.h"
#include "quadTreeNode.h"

QuadTreeNode::QuadTreeNode(PyObject *patch, int lod, int density, LPoint3d centre, double length, LVector3d normal, double offset, BoundingBox *bounds) :
    patch(patch),
    lod(lod),
    density(density),
    centre(centre),
    length(length),
    normal(normal),
    offset(offset),
    bounds(bounds),
    children(),
    children_bb(),
    children_normal(),
    children_offset(),
    shown(false),
    visible(false),
    distance(0.0),
    instance_ready(false),
    apparent_size(0.0),
    patch_in_view(false)
{
  Py_INCREF(patch);
}

QuadTreeNode::~QuadTreeNode(void)
{
  Py_DECREF(patch);
}

void
QuadTreeNode::set_shown(bool shown)
{
  this->shown = shown;
}

void
QuadTreeNode::set_instance_ready(bool instance_ready)
{
  this->instance_ready = instance_ready;
}

void
QuadTreeNode::add_child(QuadTreeNode *child)
{
  children.push_back(child);
  children_bb.push_back(DCAST(BoundingBox, child->bounds->make_copy()));
  children_normal.push_back(child->normal);
  children_offset.push_back(child->offset);
}

void
QuadTreeNode::remove_children(void)
{
  children.clear();
  children_bb.clear();
  children_normal.clear();
  children_offset.clear();
}

bool
QuadTreeNode::can_merge_children(void)
{
  if (children.size() == 0) {
      return false;
  }
  for (auto child : children) {
      if (child->children.size() != 0) {
          return false;
      }
  }
  return true;
}

bool
QuadTreeNode::in_patch(LPoint2d local)
{
  return false;
}

void
QuadTreeNode::check_visibility(CullingFrustumBase *culling_frustum, LPoint2d local, LPoint3d model_camera_pos, LVector3d model_camera_vector, double altitude, double pixel_size)
{
  bool within_patch = false;
  if (false && in_patch(local)) {
      within_patch = true;
      distance = altitude;
  } else {
      distance = max(altitude, (centre - model_camera_pos).length() - length * 0.7071067811865476);
  }
  patch_in_view = culling_frustum->is_patch_in_view(this);
  visible = within_patch || patch_in_view;
  apparent_size = length / (distance * pixel_size);
}

bool
QuadTreeNode::are_children_visibles(CullingFrustumBase *culling_frustum)
{
  bool children_visible = children_bb.size() == 0;
  for (unsigned int i = 0; i < children_bb.size(); ++i) {
      if (culling_frustum->is_bb_in_view(children_bb[i], children_normal[i], children_offset[i])) {
          children_visible = true;
          break;
      }
  }
  return children_visible;
}

void
QuadTreeNode::check_lod(LodResult *lod_result, CullingFrustumBase *culling_frustum, LPoint2d local, LPoint3d model_camera_pos, LVector3d model_camera_vector, double altitude, double pixel_size, LodControl *lod_control)
{
  check_visibility(culling_frustum, local, model_camera_pos, model_camera_vector, altitude, pixel_size);
  lod_result->check_max_lod(this);
  if (children.size() != 0) {
      if (can_merge_children() && lod_control->should_merge(this, apparent_size, distance)) {
          lod_result->add_to_merge(this);
      } else {
          for (auto child : children) {
              child->check_lod(lod_result, culling_frustum, local, model_camera_pos, model_camera_vector, altitude, pixel_size, lod_control);
          }
      }
  } else {
      if (lod_control->should_split(this, apparent_size, distance) && (lod > 0 || instance_ready)) {
          if (are_children_visibles(culling_frustum)) {
              lod_result->add_to_split(this);
          }
      }
      if (shown && lod_control->should_remove(this, apparent_size, distance)) {
          lod_result->add_to_remove(this);
      }
      if (!shown && lod_control->should_instanciate(this, apparent_size, distance)) {
          lod_result->add_to_show(this);
      }
  }
}
