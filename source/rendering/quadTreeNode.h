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

#ifndef PATCH_H
#define PATCH_H

#include "pandabase.h"
#include "luse.h"
#include "referenceCount.h"
#include "boundingBox.h"
#include <vector>
#include "py_panda.h"

class CullingFrustumBase;
class LodControl;
class LodResult;

class QuadTreeNode : public ReferenceCount
{
PUBLISHED:
  QuadTreeNode(PyObject *patch, unsigned int lod, unsigned int density, LPoint3d centre, double length, LVector3d offset_vector, double offset, BoundingBox *bounds);
  virtual ~QuadTreeNode(void);

  void set_shown(bool shown);

  void set_instance_ready(bool instance_ready);

  void add_child(QuadTreeNode *child);

  void remove_children(void);

  bool can_merge_children(void);

  bool in_patch(LPoint2d local);

  void check_visibility(CullingFrustumBase *culling_frustum, LPoint2d local, LPoint3d model_camera_pos, LVector3d model_camera_vector, double altitude, double pixel_size);

  bool are_children_visibles(CullingFrustumBase *culling_frustum);

  void check_lod(LodResult *lod_result, CullingFrustumBase *culling_frustum, LPoint2d local, LPoint3d model_camera_pos, LVector3d model_camera_vector, double altitude, double pixel_size, LodControl *lod_control);

  INLINE PyObject *get_patch(void);

  INLINE BoundingBox *get_bounds(void);

  MAKE_PROPERTY(patch, get_patch);
  MAKE_PROPERTY(bounds, get_bounds);

PUBLISHED:
  unsigned int lod;
  unsigned int density;
  LPoint3d centre;
  double length;
  LVector3d offset_vector;
  double offset;
  bool shown;
  bool visible;
  double distance;
  bool instance_ready;
  double apparent_size;
  bool patch_in_view;

public:
  PyObject *patch;
  PT(BoundingBox) bounds;
  std::vector<PT(QuadTreeNode)> children;
  std::vector<PT(BoundingBox)> children_bb;
  std::vector<LVector3d> children_offset_vector;
  std::vector<double> children_offset;
};

INLINE PyObject *QuadTreeNode::get_patch(void)
{
  Py_INCREF(patch);
  return patch;
}

INLINE BoundingBox *QuadTreeNode::get_bounds(void)
{
  return bounds;
}

#endif //PATCH_H

