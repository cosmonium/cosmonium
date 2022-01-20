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


from ..shapes import Shape
from ..pstats import pstat


class QuadTreeNode:
    def __init__(self, patch, lod, density, centre, length, normal, offset, bounds):
        Shape.__init__(self)
        self.patch = patch
        self.lod = lod
        self.density = density
        self.centre = centre
        self.length = length
        self.normal = normal
        self.offset = offset
        self.bounds = bounds
        self.children = []
        self.children_bb = []
        self.children_normal = []
        self.children_offset = []
        self.shown = False
        self.visible = False
        self.distance = 0.0
        self.instance_ready = False
        self.apparent_size = None
        self.patch_in_view = False

    def set_shown(self, shown):
        self.shown = shown

    def set_instance_ready(self, instance_ready):
        self.instance_ready = instance_ready

    def add_child(self, child):
        self.children.append(child)
        self.children_bb.append(child.bounds.make_copy())
        self.children_normal.append(child.normal)
        self.children_offset.append(child.offset)

    def remove_children(self):
        self.children = []
        self.children_bb = []
        self.children_normal = []
        self.children_offset = []

    def can_merge_children(self):
        if len(self.children) == 0:
            return False
        for child in self.children:
            if len(child.children) != 0:
                return False
        return True

    def in_patch(self, x, y):
        return x >= self.x0 and x <= self.x1 and y >= self.y0 and y <= self.y1

    def check_visibility(self, culling_frustum, local, model_camera_pos, model_camera_vector, altitude, pixel_size):
        #Testing if we are inside the patch create visual artifacts
        #The change of lod between patches is too noticeable
        if False and self.in_patch(*local):
            within_patch = True
            self.distance = altitude
        else:
            within_patch = False
            self.distance = max(altitude, (self.centre - model_camera_pos).length() - self.length * 0.7071067811865476)
        self.patch_in_view = culling_frustum.is_patch_in_view(self)
        self.visible = within_patch or self.patch_in_view
        self.apparent_size = self.length / (self.distance * pixel_size)

    def are_children_visibles(self, culling_frustum):
        children_visible = len(self.children_bb) == 0
        for (i, child_bb) in enumerate(self.children_bb):
            if culling_frustum.is_bb_in_view(child_bb, self.children_normal[i], self.children_offset[i]):
                children_visible = True
                break
        return children_visible

    @pstat
    def check_lod(self, lod_result, culling_frustum, local, model_camera_pos, model_camera_vector, altitude, pixel_size, lod_control):
        self.check_visibility(culling_frustum, local, model_camera_pos, model_camera_vector, altitude, pixel_size)
        lod_result.check_max_lod(self)
        if len(self.children) != 0:
            if self.can_merge_children() and lod_control.should_merge(self, self.apparent_size, self.distance):
                lod_result.add_to_merge(self)
            else:
                for child in self.children:
                    child.check_lod(lod_result, culling_frustum, local, model_camera_pos, model_camera_vector, altitude, pixel_size, lod_control)
        else:
            if self.visible and lod_control.should_split(self, self.apparent_size, self.distance) and (self.lod > 0 or self.instance_ready):
                if self.are_children_visibles(culling_frustum):
                    lod_result.add_to_split(self)
            if self.shown and lod_control.should_remove(self, self.apparent_size, self.distance):
                lod_result.add_to_remove(self)
            if not self.shown and lod_control.should_instanciate(self, self.apparent_size, self.distance):
                lod_result.add_to_show(self)
