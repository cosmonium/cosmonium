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

from panda3d.core import LPoint3d
from math import sqrt

class Octree(object):
    max_level = 200
    max_leaves = 75
    coef = sqrt(3)
    nb_cells = 0
    nb_leaves = 0
    def __init__(self, level, center, width, threshold, index = -1):
        self.level = level
        self.width = width
        self.half_width = width / 2.0
        self.radius = self.half_width * self.coef
        self.center = center
        self.threshold = threshold
        self.child_threshold = threshold + 0.5 # + 1.5 #Correspond roughly to 1/4 less luminosity
        self.index = index
        self.has_children = False
        self.children = [None, None, None, None, None, None, None, None]
        self.leaves = []
        self.max_magnitude = 99.0
        self.update_id = 0
        Octree.nb_cells += 1

    def add_in_child(self, obj, position, magnitude):
        index = 0
        if position.x >= self.center.x: index |= 1
        if position.y >= self.center.y: index |= 2
        if position.z >= self.center.z: index |= 4
        if self.children[index] is None:
            child_offset = self.half_width / 2.0
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
            child = Octree(self.level + 1, child_center, self.half_width, self.child_threshold, index)
            self.children[index] = child
            Octree.nb_cells += 1
        self.children[index].add(obj, position, magnitude)

    def add(self, obj, position, magnitude):
        self.nb_leaves += 1
        if magnitude < self.max_magnitude:
            self.max_magnitude = magnitude
        if not self.has_children or magnitude < self.threshold:
            self.leaves.append(obj)
        else:
            self.add_in_child(obj, position, magnitude)
        if self.level < self.max_level and len(self.leaves) >= self.max_leaves and not self.has_children:
            self.split()

    def split(self):
        new_leaves = []
        for leaf in self.leaves:
            if leaf.get_abs_magnitude() < self.threshold:
                new_leaves.append(leaf)
            else:
                self.add_in_child(leaf, leaf.get_global_position(), leaf.get_abs_magnitude())
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
