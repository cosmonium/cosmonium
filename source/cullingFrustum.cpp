#include "boundingVolume.h"
#include "boundingBox.h"
#include "boundingHexahedron.h"
#include "dcast.h"
#include "lens.h"

#include "cullingFrustum.h"
#include "patch.h"

CullingFrustumBase::~CullingFrustumBase(void)
{
}

bool
CullingFrustumBase::is_patch_in_view(QuadTreeNode *patch)
{
  return is_bb_in_view(patch->bounds, patch->normal, patch->offset);
}

CullingFrustum::CullingFrustum(Lens *lens, LMatrix4 transform_mat, bool offset_body_center, LVector3d model_body_center_offset, bool shift_patch_origin) :
    lens(lens),
    offset_body_center(offset_body_center),
    model_body_center_offset(model_body_center_offset),
    shift_patch_origin(shift_patch_origin)
{
  lens_bounds = lens->make_bounds();
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
  //offset = LPoint3(*offset);
  BoundingBox obj_bounds(bb->get_min() + offset, bb->get_max() + offset);
  int intersect = lens_bounds->contains(&obj_bounds);
  return (intersect & BoundingVolume::IF_some) != 0;
}

HorizonCullingFrustum::HorizonCullingFrustum(Lens *lens, double scale, LMatrix4 transform_mat, double min_radius, double altitude_to_min_radius, unsigned int max_lod,
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
  double far = limit * scale;
  //Set the near plane to lens-far-limit * 10 * far to optmimize the size of the frustum
  //TODO: get the actual value from the config
  this->lens->set_near_far(far * 1e-6, far);
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
  //offset = LPoint3(*offset);
  BoundingBox obj_bounds(bb->get_min() + offset, bb->get_max() + offset);
  int intersect = lens_bounds->contains(&obj_bounds);
  return (intersect & BoundingVolume::IF_some) != 0;
}
