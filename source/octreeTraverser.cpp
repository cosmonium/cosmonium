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

#include "octreeTraverser.h"
#include "octreeLeaf.h"
#include "octreeNode.h"
#include "infiniteFrustum.h"
#include "astro.h"

#include "iostream"

VisibleObjectsTraverser::VisibleObjectsTraverser(InfiniteFrustum const &frustum, double limit, unsigned int update_id) :
    frustum(frustum),
    limit(limit),
    update_id(update_id),
    collected_leaves()
{
}

int
VisibleObjectsTraverser::get_num_leaves(void) const
{
  return collected_leaves.size();
}

PT(OctreeLeaf)
VisibleObjectsTraverser::get_leaf(int index) const
{
  return collected_leaves[index];
}

bool
VisibleObjectsTraverser::enter(OctreeNode const &octree) const
{
  double distance = (octree.center - frustum.get_position()).length() - octree.radius;
  if (distance <= 0.0) {
    return true;
  }
  if (abs_to_app_mag(octree.max_magnitude, distance) > limit) {
    return false;
  }
  return frustum.is_sphere_in(octree.center, octree.radius);
}

void
VisibleObjectsTraverser::traverse(OctreeNode &octree, std::vector<PT(OctreeLeaf)> &leaves)
{
  double distance = (octree.center - frustum.get_position()).length() - octree.radius;
  double faintest;
  if (distance > 0.0) {
    faintest = app_to_abs_mag(limit, distance);
  } else {
    faintest = 99.0;
  }
  for (auto leaf : leaves) {
    double abs_magnitude = leaf->get_abs_magnitude();
    bool add = false;
    if (abs_magnitude < faintest) {
      LVector3d direction = leaf->get_global_position() - frustum.get_position();
      double distance = direction.length();
      if (distance > 0.0) {
        leaf->app_magnitude = abs_to_app_mag(abs_magnitude, distance);
        if (leaf->app_magnitude < limit) {
          add = frustum.is_sphere_in(leaf->get_global_position(), leaf->get_extend());
        }
      } else {
        add = true;
      }
    }
    if(add) {
      collected_leaves.push_back(leaf);
      leaf->set_update_id(update_id);
    }
  }
}

void
VisibleObjectsTraverser::update_pos_and_visibility(LPoint3d camera_global_pos, LPoint3d camera_position, double pixel_size, double min_body_size)
{
  for (auto leaf : collected_leaves) {
    leaf->update_pos_and_visibility(camera_global_pos, camera_position, pixel_size, min_body_size);
  }
}

void
VisibleObjectsTraverser::update_scene_info(double midPlane, double scale)
{
  for (auto leaf : collected_leaves) {
    leaf->update_scene_info(midPlane, scale);
  }
}
