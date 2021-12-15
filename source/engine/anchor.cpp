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

#include "anchor.h"
#include "py_panda.h"

TypeHandle AnchorTreeBase::_type_handle;

AnchorTreeBase::AnchorTreeBase(unsigned int anchor_class) :
  content(anchor_class),
  parent(nullptr),
  rebuild_needed(false)
{
}

AnchorTreeBase::~AnchorTreeBase(void)
{
}

AnchorTreeBase *
AnchorTreeBase::get_parent(void)
{
  return parent;
}

void
AnchorTreeBase::set_parent(AnchorTreeBase *parent)
{
  this->parent = parent;
}

void
AnchorTreeBase::set_rebuild_needed(void)
{
    rebuild_needed = true;
    if (parent != 0) {
        parent->set_rebuild_needed();
    }
}

TypeHandle AnchorBase::_type_handle;

AnchorBase::AnchorBase(unsigned int anchor_class, PyObject *ref_object) :
  AnchorTreeBase(anchor_class),
  ref_object(ref_object),
  //Flags
  was_visible(false),
  visible(false),
  visibility_override(false),
  was_resolved(false),
  resolved(false),
  update_id(~0),
  update_frozen(false),
  force_update(false),
  //Cached values
  _position(0.0),
  _global_position(0.0),
  _local_position(0.0),
  _orientation(LQuaterniond::ident_quat()),
  _extend(0.0),
  _height_under(0.0),
  //Scene parameters
  rel_position(0.0),
  distance_to_obs(0.0),
  vector_to_obs(0.0),
  visible_size(0.0),
  z_distance(0.0)
{
  Py_INCREF(ref_object);
}

AnchorBase::~AnchorBase(void)
{
  Py_DECREF(ref_object);
}

PyObject *
AnchorBase::get_object(void) const
{
  Py_INCREF(ref_object);
  return ref_object;
}

void
AnchorBase::set_body(PyObject *ref_object)
{
  Py_DECREF(this->ref_object);
  this->ref_object = ref_object;
  Py_INCREF(this->ref_object);
}

LPoint3d
AnchorBase::calc_absolute_relative_position(AnchorBase *anchor)
{
  LPoint3d reference_point_delta = anchor->get_absolute_reference_point() - _global_position;
  LPoint3d local_delta = anchor->get_local_position() - get_local_position();
  LPoint3d delta = reference_point_delta + local_delta;
  return delta;
}

LPoint3d
AnchorBase::calc_absolute_relative_position_to(LPoint3d position)
{
  return (get_absolute_reference_point() - position) + get_local_position();
}

void
AnchorBase::update_and_update_observer(double time, CameraAnchor &observer, unsigned long int update_id)
{
  update(time, update_id);
  update_observer(observer, update_id);
}
