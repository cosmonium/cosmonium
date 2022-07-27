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

#include "boundingVolume.h"
#include "boundingBox.h"
#include "boundingHexahedron.h"
#include "dcast.h"
#include "lens.h"

#include "cullingFrustum.h"
#include "quadTreeNode.h"

CullingFrustumBase::~CullingFrustumBase(void)
{
}

bool
CullingFrustumBase::is_patch_in_view(QuadTreeNode *patch)
{
  return is_bb_in_view(patch->bounds, patch->normal, patch->offset);
}

CullingFrustum::CullingFrustum(Lens *lens, LMatrix4 transform_mat, double near_distance, double far_distance,
    bool offset_body_center, LVector3d model_body_center_offset, bool shift_patch_origin) :
    offset_body_center(offset_body_center),
    model_body_center_offset(model_body_center_offset),
    shift_patch_origin(shift_patch_origin)
{
  this->lens = lens->make_copy();
  this->lens->set_near_far(near_distance, far_distance);
  lens_bounds = this->lens->make_bounds();
  DCAST(BoundingHexahedron, lens_bounds)->xform(transform_mat);
}

bool
CullingFrustum::is_bb_in_view(BoundingBox *bb, LVector3d patch_normal, double patch_offset)
{
  LVector3d offset(0);
  if (offset_body_center) {
    offset += model_body_center_offset;
  }
  if (shift_patch_origin) {
    offset = offset + patch_normal * patch_offset;
  }
  BoundingBox obj_bounds(bb->get_min() + LCAST(PN_stdfloat, offset), bb->get_max() + LCAST(PN_stdfloat, offset));
  int intersect = lens_bounds->contains(&obj_bounds);
  return (intersect & BoundingVolume::IF_some) != 0;
}

HorizonCullingFrustum::HorizonCullingFrustum(Lens *lens, LMatrix4 transform_mat,
    double near_distance, double min_radius, double altitude_to_min_radius, double scale, unsigned int max_lod,
    bool offset_body_center, LVector3d model_body_center_offset, bool shift_patch_origin,
    bool cull_far_patches, unsigned int cull_far_patches_threshold) :
    offset_body_center(offset_body_center),
    model_body_center_offset(model_body_center_offset),
    shift_patch_origin(shift_patch_origin)
{
  this->lens = lens->make_copy();
  double factor;
  if (cull_far_patches && max_lod > cull_far_patches_threshold) {
      factor = 2.0 / (1 << ((max_lod - cull_far_patches_threshold) / 2));
  } else {
      factor = 2.0;
  }
  double limit = sqrt(max(0.001, (factor * min_radius + altitude_to_min_radius) * altitude_to_min_radius));
  double far_distance = limit * scale;
  this->lens->set_near_far(near_distance, far_distance);
  lens_bounds = this->lens->make_bounds();
  DCAST(BoundingHexahedron, lens_bounds)->xform(transform_mat);
}

bool
HorizonCullingFrustum::is_bb_in_view(BoundingBox *bb, LVector3d patch_normal, double patch_offset)
{
  LVector3d offset(0);
  if (offset_body_center) {
    offset += model_body_center_offset;
  }
  if (shift_patch_origin) {
    offset = offset + patch_normal * patch_offset;
  }
  BoundingBox obj_bounds(bb->get_min() + LCAST(PN_stdfloat, offset), bb->get_max() + LCAST(PN_stdfloat, offset));
  int intersect = lens_bounds->contains(&obj_bounds);
  return (intersect & BoundingVolume::IF_some) != 0;
}
