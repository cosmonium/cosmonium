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

#ifndef OCTREE_TRAVERSER_H
#define OCTREE_TRAVERSER_H

#include "pandabase.h"
#include "luse.h"

#include <vector>

class OctreeNode;
class OctreeLeaf;
class InfiniteFrustum;

class OctreeTraverser
{
PUBLISHED:
  virtual ~OctreeTraverser(void) {}

  virtual bool enter(OctreeNode const &octree) const = 0;
  virtual void traverse(OctreeNode &octree, std::vector<PT(OctreeLeaf)> &leaves) = 0;
};

class VisibleObjectsTraverser : public OctreeTraverser
{
PUBLISHED:
  VisibleObjectsTraverser(InfiniteFrustum const &frustum, double limit, unsigned int update_id);
  virtual ~VisibleObjectsTraverser(void) {}

  int get_num_leaves(void) const;
  PT(OctreeLeaf) get_leaf(int index) const;

  MAKE_SEQ(get_leaves, get_num_leaves, get_leaf);

  void update_pos_and_visibility(LPoint3d camera_global_pos, LPoint3d camera_position, double pixel_size, double min_body_size);
  void update_scene_info(double midPlane, double scale);

public:
  virtual bool enter(OctreeNode const &octree) const;
  virtual void traverse(OctreeNode &octree, std::vector<PT(OctreeLeaf)> &leaves);

protected:
  InfiniteFrustum const &frustum;
  double limit;
  unsigned int update_id;

  std::vector<PT(OctreeLeaf)> collected_leaves;
};

#endif //OCTREE_TRAVERSER_H
