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

#include "octreeLeaf.h"
#include "py_panda.h"

OctreeLeaf::OctreeLeaf(PyObject *ref_object, LPoint3d position, double magnitude, double extend) :
  ref_object(ref_object),
  position(position),
  magnitude(magnitude),
  extend(extend),
  update_id(0)
{
  Py_INCREF(ref_object);
}

OctreeLeaf::~OctreeLeaf(void)
{
  Py_DECREF(ref_object);
}

PyObject *
OctreeLeaf::get_object(void) const
{
  Py_INCREF(ref_object);
  return ref_object;
}
