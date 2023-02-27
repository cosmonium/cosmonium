#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2021 Laurent Deru.
#
#Cosmonium is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Cosmonium is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#


from panda3d.core import LVector3d, LPoint3
from panda3d.core import BoundingBox

from math import sqrt


class CullingFrustumBase:
    def is_bb_in_view(self, bb, patch_normal, patch_offset):
        raise NotImplementedError()

    def is_patch_in_view(self, patch):
        return self.is_bb_in_view(patch.bounds, patch.normal, patch.offset)

class CullingFrustum(CullingFrustumBase):
    def __init__(self, lens, transform_mat, near, far, offset_body_center, model_body_center_offset, shift_patch_origin):
        self.lens = lens.make_copy()
        self.lens.set_near_far(near, far)
        self.lens_bounds = self.lens.make_bounds()
        self.lens_bounds.xform(transform_mat)
        self.offset_body_center = offset_body_center
        self. model_body_center_offset = model_body_center_offset
        self.shift_patch_origin = shift_patch_origin

    def is_bb_in_view(self, bb, patch_normal, patch_offset):
        offset = LVector3d()
        if self.offset_body_center:
            offset += self.model_body_center_offset
        if self.shift_patch_origin:
            offset = offset + patch_normal * patch_offset
        offset = LPoint3(*offset)
        obj_bounds = BoundingBox(bb.get_min() + offset, bb.get_max() + offset)
        intersect = self.lens_bounds.contains(obj_bounds)
        return (intersect & BoundingBox.IF_some) != 0

class HorizonCullingFrustum(CullingFrustumBase):
    def __init__(self, lens, transform_mat, near, max_radius, altitude_to_min_radius, scale, max_lod, offset_body_center, model_body_center_offset, shift_patch_origin, cull_far_patches, cull_far_patches_threshold):
        self.lens = lens.make_copy()
        if cull_far_patches and max_lod > cull_far_patches_threshold:
            factor = 2.0 / (1 << ((max_lod - cull_far_patches_threshold) // 2))
        else:
            factor = 2.0
        limit = sqrt(max(0.001, (factor * max_radius + altitude_to_min_radius) * altitude_to_min_radius))
        far = limit * scale
        self.lens.set_near_far(near, far)
        self.lens_bounds = self.lens.make_bounds()
        self.lens_bounds.xform(transform_mat)
        self.offset_body_center = offset_body_center
        self.model_body_center_offset = model_body_center_offset
        self.shift_patch_origin = shift_patch_origin

    def is_bb_in_view(self, bb, patch_normal, patch_offset):
        offset = LVector3d()
        if self.offset_body_center:
            offset += self.model_body_center_offset
        if self.shift_patch_origin:
            offset = offset + patch_normal * patch_offset
        offset = LPoint3(*offset)
        obj_bounds = BoundingBox(bb.get_min() + offset, bb.get_max() + offset)
        intersect = self.lens_bounds.contains(obj_bounds)
        return (intersect & BoundingBox.IF_some) != 0
