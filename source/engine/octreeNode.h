/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2022 Laurent Deru.
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
#include "anchor.h"

#include <vector>

class StellarAnchor;
class AnchorTraverser;

class OctreeNode : public AnchorTreeBase
{
PUBLISHED:
  OctreeNode(int level, OctreeNode *parent, LPoint3d center, double width, double threshold, int index = -1);
  ~OctreeNode(void);

  void set_rebuild_needed(void);
  void rebuild(void);
  void traverse(AnchorTraverser &traverser);

  void add(StellarAnchor *anchor);

  size_t get_num_children(void) const;
  size_t get_num_leaves(void) const;
  OctreeNode *get_child(int index);
  StellarAnchor *get_leaf(int index) const;

  MAKE_SEQ(get_leaves, get_num_leaves, get_leaf);

  void output(std::ostream &out) const;
  void write(std::ostream &out, int indent_level = 0) const;

protected:
  void add_in_child(StellarAnchor *leaf, LPoint3d const &position, double magnitude);
  void _add(StellarAnchor *leaf, LPoint3d const &position, double magnitude);
  void split(void);

PUBLISHED:
    static int max_level;
    static int max_leaves;
    static double child_factor;

PUBLISHED:
    int level;
    double width;
    double radius;
    LPoint3d center;
    double threshold;
    int index;
    bool has_children;
    double max_luminosity;

protected:
    PT(OctreeNode) children[8];
    std::vector<PT(StellarAnchor)> leaves;
};

inline std::ostream &operator << (std::ostream &out, const OctreeNode &octree)
{
    octree.output(out);
    return out;
}

#endif // OCTREE_H
