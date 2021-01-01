#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2019 Laurent Deru.
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

from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import LPoint3d

from ..astro.astro import abs_to_app_mag, app_to_abs_mag

from math import sqrt

def OctreeLeaf(ref_object, *args):
    #TODO: We should use the actual anchor as leaf...
    ref_object.anchor._global_position = args[0]
    ref_object.anchor._abs_magnitude = args[1]
    return ref_object

class OctreeNode(object):
    max_level = 200
    max_leaves = 75
    nb_cells = 0
    nb_leaves = 0
    child_threshold = 0.5 # + 1.5 #Correspond roughly to 1/4 less luminosity
    def __init__(self, level, center, width, threshold, index = -1):
        self.level = level
        self.width = width
        self.radius = self.width / 2.0 * sqrt(3)
        self.center = center
        self.threshold = threshold
        self.index = index
        self.has_children = False
        self.children = [None, None, None, None, None, None, None, None]
        self.leaves = []
        self.max_magnitude = 99.0
        OctreeNode.nb_cells += 1

    def get_num_children(self):
        nb_children = 0
        for child in self.children:
            if child is not None:
                nb_children += 1
        return nb_children

    def get_num_leaves(self):
        return len(self.leaves)

    def traverse(self, traverser):
        traverser.traverse(self, self.leaves)
        for child in self.children:
            if child is not None and traverser.enter(child):
                child.traverse(traverser)

    def add(self, leaf):
        self._add(leaf, leaf._global_position, leaf._abs_magnitude)

    def get_child(self, index):
        return self.children[index]

    def get_leaf(self, index):
        return self.leaves[index]

    def get_leaves(self):
        return self.leaves

    def _add_in_child(self, obj, position, magnitude):
        index = 0
        if position.x >= self.center.x: index |= 1
        if position.y >= self.center.y: index |= 2
        if position.z >= self.center.z: index |= 4
        if self.children[index] is None:
            child_offset = self.width / 4.0
            child_center = LPoint3d(self.center)
            if (index & 1) != 0:
                child_center.x += child_offset
            else:
                child_center.x -= child_offset
            if (index & 2) != 0:
                child_center.y += child_offset
            else:
                child_center.y -= child_offset
            if (index & 4) != 0:
                child_center.z += child_offset
            else:
                child_center.z -= child_offset
            child = OctreeNode(self.level + 1, child_center, self.width / 2.0, self.threshold + self.child_threshold, index)
            self.children[index] = child
        self.children[index]._add(obj, position, magnitude)

    def _add(self, obj, position, magnitude):
        self.nb_leaves += 1
        if magnitude < self.max_magnitude:
            self.max_magnitude = magnitude
        if not self.has_children or magnitude < self.threshold:
            self.leaves.append(obj)
        else:
            self._add_in_child(obj, position, magnitude)
        if self.level < self.max_level and len(self.leaves) >= self.max_leaves and not self.has_children:
            self._split()

    def _split(self):
        new_leaves = []
        center = self.center
        for leaf in self.leaves:
            position = leaf._global_position
            if leaf._abs_magnitude < self.threshold or (center - position).length() < leaf._extend:
                new_leaves.append(leaf)
            else:
                self._add_in_child(leaf, position, leaf._abs_magnitude)
        self.leaves = new_leaves
        self.has_children = True

    def dump_octree_summary(self):
        if len(self.leaves) > 0:
            print(' ' * self.level, self.level, self.index, self.width, self.threshold, len(self.leaves), self.center)
        for i in range(8):
            if self.children[i] is not None:
                self.children[i].dump_octree_summary()

    def dump_octree(self):
        if len(self.leaves) > 0:
            print(' ' * self.level, self.level, self.index, self.width, self.threshold, self.center, self.has_children)
            print(' ' * self.level, '->', self.max_magnitude, ":", ', '.join(map(lambda x: x.get_name(), self.leaves)))
        for i in range(8):
            if self.children[i] is not None:
                self.children[i].dump_octree()

    def print_stats(self):
        print("Nb cells:", self.nb_cells)
        print("Nb leaves:", self.nb_leaves)

class VisibleObjectsTraverser(object):
    def __init__(self, frustum, limit, update_id):
        self.frustum = frustum
        self.limit = limit
        self.update_id = update_id
        self.collected_leaves = []

    def get_num_leaves(self):
        return len(self.collected_leaves)

    def get_leaf(self, index):
        return self.collected_leaves[index]

    def get_leaves(self):
        return self.collected_leaves

    def get_objects(self):
        return self.collected_leaves

    def enter(self, octree):
        distance = (octree.center - self.frustum.get_position()).length() - octree.radius
        if distance <= 0.0:
            return True
        if abs_to_app_mag(octree.max_magnitude, distance) > self.limit:
            return False
        return self.frustum.is_sphere_in(octree.center, octree.radius)

    def traverse(self, octree, leaves):
        frustum = self.frustum
        frustum_position = frustum.get_position()
        distance = (octree.center - frustum_position).length() - octree.radius
        if distance > 0.0:
            faintest = app_to_abs_mag(self.limit, distance)
        else:
            faintest = 99.0
        for leaf in leaves:
            abs_magnitude = leaf._abs_magnitude
            add = False
            if abs_magnitude < faintest:
                direction = leaf._global_position - frustum_position
                distance = direction.length()
                if distance > 0.0:
                    app_magnitude = abs_to_app_mag(abs_magnitude, distance)
                    if app_magnitude < self.limit:
                        add = self.frustum.is_sphere_in(leaf._global_position, leaf._extend)
                else:
                    add = True
            if add:
                self.collected_leaves.append(leaf)
                leaf.update_id = self.update_id
