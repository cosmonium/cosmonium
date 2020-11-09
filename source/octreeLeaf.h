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
  OctreeLeaf(PyObject *ref_object, LPoint3d position, double abs_magnitude, double extend, LColor point_color);
  ~OctreeLeaf(void);

  PyObject *get_object(void) const;
  void update_pos_and_visibility(LPoint3d camera_global_pos, LPoint3d camera_position, double pixel_size, double min_body_size);
  void update_scene_info(double midPlane, double scale);

  LPoint3d get_global_position(void) const { return position; }
  double get_abs_magnitude(void) const { return abs_magnitude; }
  double get_extend(void) const { return extend; }
  LColor get_point_color(void) const { return point_color; }
  unsigned int get_update_id(void) const { return update_id; }
  void set_update_id(unsigned int new_update_id) { update_id = new_update_id; }

protected:
    PyObject *ref_object;
    LPoint3d position;
    double abs_magnitude;
    double extend;
    LColor point_color;
    unsigned int update_id;

PUBLISHED:
    LVector3d vector_to_obs;
    double distance_to_obs;
    LVector3d rel_position;
    double app_magnitude;
    bool visible;
    bool resolved;
    double visible_size;
    LPoint3d scene_position;
    double scene_distance;
    double scene_scale_factor;
    LQuaterniond scene_orientation;
};

#endif //OCTREE_LEAF_H
