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

#ifndef CULLING_FRUSTUM_H
#define CULLING_FRUSTUM_H

#include "pandabase.h"
#include "luse.h"
#include "referenceCount.h"

class BoundingVolume;
class BoundingBox;
class Lens;
class QuadTreeNode;

class CullingFrustumBase : public ReferenceCount
{
PUBLISHED:
    virtual ~CullingFrustumBase(void);
    virtual bool is_bb_in_view(BoundingBox *bb, LVector3d patch_normal, double patch_offset) = 0;

    virtual bool is_patch_in_view(QuadTreeNode *node);
};

class CullingFrustum : public CullingFrustumBase
{
PUBLISHED:
    CullingFrustum(Lens *lens, LMatrix4 transform_mat, double near_distance, double far_distance,
        bool offset_body_center, LVector3d model_body_center_offset, bool shift_patch_origin);
    virtual bool is_bb_in_view(BoundingBox *bb, LVector3d patch_normal, double patch_offset);

    INLINE Lens *get_lens(void) { return lens; }

    MAKE_PROPERTY(lens, get_lens);

protected:
    PT(Lens) lens;
    PT(BoundingVolume) lens_bounds;
    bool offset_body_center;
    LVector3d model_body_center_offset;
    bool shift_patch_origin;
};

class HorizonCullingFrustum : public CullingFrustumBase
{
PUBLISHED:
    HorizonCullingFrustum(Lens *lens, LMatrix4 transform_mat,
        double near_distance, double max_radius, double altitude_to_min_radius, double scale, unsigned int max_lod,
        bool offset_body_center, LVector3d model_body_center_offset, bool shift_patch_origin,
        bool cull_far_patches, unsigned int cull_far_patches_threshold);
    virtual bool is_bb_in_view(BoundingBox *bb, LVector3d patch_normal, double patch_offset);

    INLINE Lens *get_lens(void) { return lens; }

    MAKE_PROPERTY(lens, get_lens);

protected:
    PT(Lens) lens;
    PT(BoundingVolume) lens_bounds;
    bool offset_body_center;
    LVector3d model_body_center_offset;
    bool shift_patch_origin;
};

#endif //CULLING_FRUSTUM_H

