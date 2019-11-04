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

#ifndef OCTREE_LEAF_H
#define OCTREE_LEAF_H

#include "pandabase.h"
#include "luse.h"
#include "referenceCount.h"

class OctreeLeaf : public ReferenceCount
{
PUBLISHED:
  OctreeLeaf(PyObject *ref_object, LPoint3d position, double magnitude, double extend);
  ~OctreeLeaf(void);

  PyObject *get_object(void) const;

  LPoint3d get_global_position(void) const { return position; }
  double get_abs_magnitude(void) const { return magnitude; }
  double get_extend(void) const { return extend; }
  unsigned int get_update_id(void) const { return update_id; }
  void set_update_id(unsigned int new_update_id) { update_id = new_update_id; }

protected:
    PyObject *ref_object;
    LPoint3d position;
    double magnitude;
    double extend;
    unsigned int update_id;
};

#endif //OCTREE_LEAF_H
