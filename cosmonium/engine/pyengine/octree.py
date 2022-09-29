#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2022 Laurent Deru.
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


from panda3d.core import LPoint3d

from math import sqrt

class OctreeNode(object):
    max_level = 200
    max_leaves = 75
    nb_cells = 0
    nb_leaves = 0
    child_factor = 0.25
    def __init__(self, level, parent, center, width, threshold, index = -1):
        self.level = level
        self.parent = parent
        self.width = width
        self.radius = self.width / 2.0 * sqrt(3)
        self.center = center
        self.threshold = threshold
        self.index = index
        self.has_children = False
        self.children = [None, None, None, None, None, None, None, None]
        self.leaves = []
        self.max_luminosity = 0.0
        self.rebuild_needed = False
        #TODO: Right now an octree contains anything
        self.content = ~0
        OctreeNode.nb_cells += 1

    def get_num_children(self):
        nb_children = 0
        for child in self.children:
            if child is not None:
                nb_children += 1
        return nb_children

    def get_num_leaves(self):
        return len(self.leaves)

    def set_rebuild_needed(self):
        self.rebuild_needed = True
        if self.parent is not None:
            self.parent.set_rebuild_needed()

    def rebuild(self):
        for child in self.children:
            if child is not None and child.rebuild_needed:
                child.rebuild()
        self.rebuild_needed = False

    def traverse(self, traverser):
        traverser.traverse_octree_node(self)
        for child in self.children:
            if child is not None and traverser.enter_octree_node(child):
                child.traverse(traverser)

    def add(self, leaf):
        self._add(leaf, leaf._global_position, leaf._intrinsic_luminosity)

    def get_child(self, index):
        return self.children[index]

    def get_leaf(self, index):
        return self.leaves[index]

    def get_leaves(self):
        return self.leaves

    def _add_in_child(self, obj, position, luminosity):
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
            child = OctreeNode(self.level + 1, self, child_center, self.width / 2.0, self.threshold * self.child_factor, index)
            self.children[index] = child
        self.children[index]._add(obj, position, luminosity)

    def _add(self, obj, position, luminosity):
        self.nb_leaves += 1
        if luminosity > self.max_luminosity:
            self.max_luminosity = luminosity
        if not self.has_children or luminosity > self.threshold:
            self.leaves.append(obj)
            obj.parent = self
        else:
            self._add_in_child(obj, position, luminosity)
        if self.level < self.max_level and len(self.leaves) >= self.max_leaves and not self.has_children:
            self._split()

    def _split(self):
        new_leaves = []
        center = self.center
        for leaf in self.leaves:
            position = leaf._global_position
            if leaf._intrinsic_luminosity > self.threshold or (center - position).length() < leaf.bounding_radius:
                new_leaves.append(leaf)
            else:
                self._add_in_child(leaf, position, leaf._intrinsic_luminosity)
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
            print(' ' * self.level, '->', self.max_luminosity, ":", ', '.join(map(lambda x: x.get_name(), self.leaves)))
        for i in range(8):
            if self.children[i] is not None:
                self.children[i].dump_octree()

    def print_stats(self):
        print("Nb cells:", self.nb_cells)
        print("Nb leaves:", self.nb_leaves)
