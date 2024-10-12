/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2023 Laurent Deru.
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


#include "frames.h"
#include "cartesianAnchor.h"
#include "cameraAnchor.h"
#include "frames.h"
#include "py_panda.h"
#include "settings.h"
#include "infiniteFrustum.h"
#include "anchorTraverser.h"
#include "stellarAnchor.h"

TypeHandle CartesianAnchor::_type_handle;

CartesianAnchor::CartesianAnchor(unsigned int anchor_class, PyObject *ref_object, ReferenceFrame *frame, LColor point_color) :
    AnchorBase(anchor_class, ref_object, point_color),
    frame(frame),
    _frame_position(0.0),
    _frame_orientation(LQuaterniond::ident_quat())
{
}

CartesianAnchor::CartesianAnchor(unsigned int anchor_class, PyObject *ref_object, ReferenceFrame *frame) :
    AnchorBase(anchor_class, ref_object, LColor(0)),
    frame(frame),
    _frame_position(0.0),
    _frame_orientation(LQuaterniond::ident_quat())
{
}

CartesianAnchor::~CartesianAnchor(void)
{
}

bool
CartesianAnchor::is_stellar(void) const
{
    return false;
}

bool
CartesianAnchor::has_orbit(void) const
{
    return false;
}

bool
CartesianAnchor::has_rotation(void) const
{
    return false;
}

bool
CartesianAnchor::has_frame(void) const
{
    return true;
}

void
CartesianAnchor::traverse(AnchorTraverser &visitor)
{
  visitor.traverse_anchor(this);
}

void
CartesianAnchor::rebuild(void)
{
}

double
CartesianAnchor::get_position_bounding_radius(void) const
{
  return 0;
}

void
CartesianAnchor::copy(CartesianAnchor const &other)
{
  frame = other.get_frame();
  _global_position = other.get_absolute_reference_point();
  _frame_position = other.get_frame_position();
  _frame_orientation = other.get_frame_orientation();
}

void
CartesianAnchor::set_frame(ReferenceFrame *frame)
{
  // Get position and rotation in the absolute reference frame
  LPoint3d pos = get_local_position();
  LQuaterniond rot = get_absolute_orientation();
  // Update reference frame
  this->frame = frame;
  // Set back the position to calculate the position in the new reference frame
  set_local_position(pos);
  set_absolute_orientation(rot);
}

void
CartesianAnchor::do_update(void)
{
    // TODO: _position should be global + local !
    _position = get_local_position();
    _local_position = get_local_position();
    _orientation = get_absolute_orientation();
}

void
CartesianAnchor::set_frame_position(LPoint3d position)
{
  _frame_position = position;
}

LPoint3d
CartesianAnchor::get_frame_position(void) const
{
  return _frame_position;
}

void
CartesianAnchor::set_frame_orientation(LQuaterniond rotation)
{
  _frame_orientation = rotation;
}

LQuaterniond
CartesianAnchor::get_frame_orientation(void) const
{
  return _frame_orientation;
}

LPoint3d
CartesianAnchor::get_local_position(void) const
{
  return frame->get_local_position(_frame_position);
}

void
CartesianAnchor::set_local_position(LPoint3d position)
{
  _frame_position = frame->get_frame_position(position);
}

LPoint3d
CartesianAnchor::get_absolute_reference_point(void) const
{
  return _global_position;
}

void
CartesianAnchor::set_absolute_reference_point(LPoint3d new_reference_point)
{
  if (new_reference_point == _global_position) {
      return;
  }
  LPoint3d old_local = frame->get_local_position(_frame_position);
  LPoint3d new_local = (_global_position - new_reference_point) + old_local;
  _global_position = new_reference_point;
  _frame_position = frame->get_frame_position(new_local);
  do_update();
}

LPoint3d
CartesianAnchor::get_absolute_position(void) const
{
  return _global_position + get_local_position();
}

void
CartesianAnchor::set_absolute_position(LPoint3d position)
{
  position -= _global_position;
  _frame_position = frame->get_frame_position(position);
}

LQuaterniond
CartesianAnchor::get_absolute_orientation(void) const
{
  return frame->get_absolute_orientation(_frame_orientation);
}

void
CartesianAnchor::set_absolute_orientation(LQuaterniond orientation)
{
  _frame_orientation = frame->get_frame_orientation(orientation);
}

LPoint3d
CartesianAnchor::calc_absolute_position_of(LPoint3d frame_position)
{
  return _global_position + frame->get_local_position(frame_position);
}

LPoint3d
CartesianAnchor::calc_relative_position_to(LPoint3d position)
{
  //TODO: Should be refactored into AnchorBase
  return (_global_position - position) + get_local_position();
}

LPoint3d
CartesianAnchor::calc_frame_position_of_absolute(LPoint3d position)
{
  return frame->get_frame_position(position - _global_position);
}

LPoint3d
CartesianAnchor::calc_frame_position_of_local(LPoint3d position)
{
  return frame->get_frame_position(position);
}

LQuaterniond
CartesianAnchor::calc_frame_orientation_of(LQuaterniond orientation)
{
  return frame->get_frame_orientation(orientation);
}

LPoint3d
CartesianAnchor::calc_local_position_of_frame(LPoint3d position)
{
  return frame->get_local_position(position);
}

void
CartesianAnchor::update(double time, unsigned long int update_id)
{
  do_update();
}

void
CartesianAnchor::update_observer(CameraAnchor &observer, unsigned long int update_id)
{
  if (update_id == this->update_id) return;
  LPoint3d reference_point_delta = _global_position - observer.get_absolute_reference_point();
  LPoint3d local_delta = _local_position - observer.get_local_position();
  rel_position = reference_point_delta + local_delta;
  distance_to_obs = rel_position.length();
  if (distance_to_obs > 0.0) {
      vector_to_obs = -rel_position / distance_to_obs;
      visible_size = bounding_radius / (distance_to_obs * observer.pixel_size);
      double coef = -vector_to_obs.dot(observer.camera_vector);
      z_distance = distance_to_obs * coef;
  } else {
      vector_to_obs = 0.0;
      visible_size = 0.0;
      z_distance = 0.0;
  }
}


void
CartesianAnchor::update_state(CameraAnchor &observer, unsigned long int update_id)
{
  was_visible = visible;
  was_resolved = resolved;
  double radius = bounding_radius;
  if (distance_to_obs > radius) {
      bool in_view = observer.rel_frustum->is_sphere_in(rel_position, radius);
      resolved = visible_size > settings.min_body_size;
      visible = in_view;
  } else {
      // We are in the object
      resolved = true;
      visible = true;
  }
}

void
CartesianAnchor::update_luminosity(StellarAnchor *star)
{
}

TypeHandle OriginAnchor::_type_handle;

OriginAnchor::OriginAnchor(unsigned int anchor_class, PyObject *ref_object) :
    CartesianAnchor(anchor_class, ref_object, new AbsoluteReferenceFrame())
{
}


TypeHandle FlatSurfaceAnchor::_type_handle;


FlatSurfaceAnchor::FlatSurfaceAnchor(unsigned int anchor_class, PyObject *ref_object, PyObject *ref_surface) :
    OriginAnchor(anchor_class, ref_object),
    ref_surface(ref_surface)
{
  if (ref_surface != nullptr) {
    Py_INCREF(ref_surface);
  }
}


FlatSurfaceAnchor::~FlatSurfaceAnchor(void)
{
  if (ref_surface != nullptr) {
    Py_DECREF(ref_surface);
  }
}


void
FlatSurfaceAnchor::set_surface(PyObject *ref_surface)
{
  if (this->ref_surface != nullptr) {
    Py_DECREF(this->ref_surface);
  }
  this->ref_surface = ref_surface;
  if (this->ref_surface != nullptr) {
    Py_INCREF(this->ref_surface);
  }
}


void
FlatSurfaceAnchor::update_observer(CameraAnchor &observer, unsigned long int update_id)
{
  if (update_id == this->update_id) return;
  vector_to_obs = observer.get_local_position();
  vector_to_obs.normalize();
  LPoint3d observer_local_position = observer.get_local_position();
  rel_position = _local_position - observer_local_position;
  distance_to_obs = rel_position.length();
  visible_size = 0.0;
  z_distance = 0.0;
}


void
FlatSurfaceAnchor::update_state(CameraAnchor &observer, unsigned long int update_id)
{
  was_visible = visible;
  was_resolved = resolved;
  visible = true;
  resolved = true;
}


TypeHandle ObserverAnchor::_type_handle;

ObserverAnchor::ObserverAnchor(unsigned int anchor_class, PyObject *ref_object) :
    CartesianAnchor(anchor_class, ref_object, new AbsoluteReferenceFrame())
{
}


void
ObserverAnchor::update(double time, unsigned long int update_id)
{
  // Do nothing
}


void
ObserverAnchor::update_observer(CameraAnchor &observer, unsigned long int update_id)
{
  if (update_id == this->update_id) return;
  copy(observer);
  distance_to_obs = 0.0;
  vector_to_obs = LVector3d();
  visible_size = 0.0;
  z_distance = 0.0;
}


void
ObserverAnchor::update_state(CameraAnchor &observer, unsigned long int update_id)
{
  was_visible = visible;
  was_resolved = resolved;
  visible = true;
  resolved = true;
}
