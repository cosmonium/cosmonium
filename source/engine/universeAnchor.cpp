/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2021 Laurent Deru.
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

#include "universeAnchor.h"
#include "octreeNode.h"


TypeHandle UniverseAnchor::_type_handle;

UniverseAnchor::UniverseAnchor(PyObject *ref_object,
    OrbitBase *orbit,
    RotationBase *rotation,
    LColor point_color) :
    OctreeAnchor(ref_object, orbit, rotation, point_color)
{
  visible = true;
  resolved = true;
}

void
UniverseAnchor::traverse(AnchorTraverser &visitor)
{
  octree->traverse(visitor);
}
