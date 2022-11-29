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

#include "octreeAnchor.h"
#include "anchorTraverser.h"
#include "octreeNode.h"
#include "astro.h"

TypeHandle OctreeAnchor::_type_handle;

OctreeAnchor::OctreeAnchor(PyObject *ref_object,
    OrbitBase *orbit,
    RotationBase *rotation,
    LColor point_color) :
    SystemAnchor(ref_object, orbit, rotation, point_color),
    recreate_octree(true)
{
  //TODO: Turn this into a parameter or infer it from the children
  bounding_radius = 100000.0 * Ly;
  //TODO: Should be configurable
  double top_level_absolute_magnitude = app_to_abs_mag(6.0, bounding_radius * sqrt(3));
  double luminosity = abs_mag_to_lum(top_level_absolute_magnitude) * L0;
  //TODO: position should be extracted from orbit
  octree = new OctreeNode(0, /*this,*/ 0,
      LPoint3d(10 * Ly, 10 * Ly, 10 * Ly),
      bounding_radius,
      luminosity);
  octree->parent = this;
  //TODO: Should be done during rebuild
  _intrinsic_luminosity = luminosity;
  //TODO: Right now an octree contains anything
  content = ~0;
  recreate_octree = true;
}

void
OctreeAnchor::traverse(AnchorTraverser &visitor)
{
  if (visitor.enter_octree_node(octree)) {
    octree->traverse(visitor);
  }
}

void
OctreeAnchor::rebuild(void)
{
  if (recreate_octree) {
    create_octree();
    recreate_octree = false;
  }
  if (octree->rebuild_needed) {
    octree->rebuild();
  }
  rebuild_needed = false;
}

void
OctreeAnchor::create_octree(void)
{
  for (auto child : children) {
    child->update(0, 0);
    child->rebuild();
    octree->add(child);
  }
}
