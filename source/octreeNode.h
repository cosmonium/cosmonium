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

#ifndef OCTREE_H
#define OCTREE_H

#include "pandabase.h"
#include "luse.h"

#include <vector>

class OctreeLeaf;
class OctreeTraverser;

class OctreeNode
{
PUBLISHED:
  OctreeNode(int level, LPoint3d center, double width, double threshold, int index = -1);
  ~OctreeNode(void);

  void add(PT(OctreeLeaf) leaf);

  size_t get_num_children(void) const;
  size_t get_num_leaves(void) const;
  void traverse(OctreeTraverser *traverser);
  OctreeNode *get_child(int index);
  PT(OctreeLeaf) get_leaf(int index) const;

  MAKE_SEQ(get_leaves, get_num_leaves, get_leaf);

  void output(std::ostream &out) const;
  void write(std::ostream &out, int indent_level = 0) const;

protected:
  void add_in_child(PT(OctreeLeaf) leaf, LPoint3d const &position, double magnitude);
  void _add(PT(OctreeLeaf) leaf, LPoint3d const &position, double magnitude);
  void split(void);

PUBLISHED:
    static int max_level;
    static int max_leaves;
    static double child_threshold;

PUBLISHED:
    int level;
    double width;
    double radius;
    LPoint3d center;
    double threshold;
    int index;
    bool has_children;
    double max_magnitude;

protected:
    OctreeNode *children[8];
    std::vector<PT(OctreeLeaf)> leaves;
};

inline std::ostream &operator << (std::ostream &out, const OctreeNode &octree)
{
    octree.output(out);
    return out;
}

#endif // OCTREE_H
