/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2025 Laurent Deru.
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
AnchorTreeBase::get_parent(void) const
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

AnchorBase::AnchorBase(unsigned int anchor_class, PyObject *ref_object, LColor point_color,
                       const pvector<std::string> names,
                       const pvector<std::string> source_names,
                       const std::string &description) :
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
  bounding_radius(0.0),
  _height_under(0.0),
  //Scene parameters
  rel_position(0.0),
  distance_to_obs(0.0),
  vector_to_obs(0.0),
  visible_size(0.0),
  z_distance(0.0),
  // Temporary
  point_color(point_color),
  _intrinsic_luminosity(0.0),
  _reflected_luminosity(0.0),
  _point_radiance(0.0),
  _albedo(0.0),
  // Name management
  description(description)
{
  Py_INCREF(ref_object);

  // Parse and add names
  if (names.empty()) {
    object_names.add_name(ObjectName::make_vernacular(""));
  } else {
    for (size_t i = 0; i < names.size(); ++i) {
      ObjectName parsed = ObjectNames::parse_name(names[i]);
      // If there's a corresponding source name, use it as the original
      if (i < source_names.size()) {
        object_names.add_name(parsed, source_names[i]);
      } else {
        object_names.add_name(parsed);
      }
    }
  }
}

AnchorBase::AnchorBase(unsigned int anchor_class, PyObject *ref_object, LColor point_color,
                       PyObject *names,
                       PyObject *source_names,
                       const std::string &description) :
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
  bounding_radius(0.0),
  _height_under(0.0),
  //Scene parameters
  rel_position(0.0),
  distance_to_obs(0.0),
  vector_to_obs(0.0),
  visible_size(0.0),
  z_distance(0.0),
  // Temporary
  point_color(point_color),
  _intrinsic_luminosity(0.0),
  _reflected_luminosity(0.0),
  _point_radiance(0.0),
  _albedo(0.0),
  // Name management
  description(description)
{
  Py_INCREF(ref_object);

  // Extract and parse names from Python list
  pvector<std::string> name_strings;
  if (names != nullptr && PyList_Check(names)) {
    Py_ssize_t size = PyList_Size(names);
    for (Py_ssize_t i = 0; i < size; ++i) {
      PyObject *item = PyList_GetItem(names, i);
      if (item != nullptr && PyUnicode_Check(item)) {
        const char *str;
        Py_ssize_t str_len;
        str = PyUnicode_AsUTF8AndSize(item, &str_len);
        if (str != nullptr) {
          name_strings.push_back(std::string(str, str_len));
        }
      }
    }
  }

  // Extract source_names from Python list
  pvector<std::string> source_name_strings;
  if (source_names != nullptr && PyList_Check(source_names)) {
    Py_ssize_t size = PyList_Size(source_names);
    for (Py_ssize_t i = 0; i < size; ++i) {
      PyObject *item = PyList_GetItem(source_names, i);
      if (item != nullptr && PyUnicode_Check(item)) {
          const char *str;
          Py_ssize_t str_len;
          str = PyUnicode_AsUTF8AndSize(item, &str_len);
        if (str != nullptr) {
          source_name_strings.push_back(std::string(str, str_len));
        }
      }
    }
  }

  // Parse and add names with originals
  if (name_strings.empty()) {
    object_names.add_name(ObjectName::make_vernacular(""));
  } else {
    for (size_t i = 0; i < name_strings.size(); ++i) {
      ObjectName parsed = ObjectNames::parse_name(name_strings[i]);
      // If there's a corresponding source name, use it as the original
      if (i < source_name_strings.size()) {
        object_names.add_name(parsed, source_name_strings[i]);
      } else {
        object_names.add_name(parsed);
      }
    }
  }
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

LColor
AnchorBase::get_point_color(void) const
{
  return point_color;
}

void
AnchorBase::set_point_color(LColor color)
{
  this->point_color = color;
}

double
AnchorBase::get_bounding_radius(void) const
{
  return bounding_radius;
}

void
AnchorBase::set_bounding_radius(double bounding_radius)
{
  this->bounding_radius = bounding_radius;
}

LPoint3d
AnchorBase::calc_absolute_relative_position(AnchorBase const *anchor) const
{
  LPoint3d reference_point_delta = anchor->get_absolute_reference_point() - _global_position;
  LPoint3d local_delta = anchor->get_local_position() - get_local_position();
  LPoint3d delta = reference_point_delta + local_delta;
  return delta;
}

LPoint3d
AnchorBase::calc_absolute_relative_position_to(LPoint3d position) const
{
  return (get_absolute_reference_point() - position) + get_local_position();
}

void
AnchorBase::update_all(double time, CameraAnchor &observer, unsigned long int update_id)
{
  update(time, update_id);
  update_observer(observer, update_id);
  update_state(observer, update_id);
}

// Name management methods implementation
pvector<std::string>
AnchorBase::_get_names(void) const
{
  return object_names.get_all_names();
}

void
AnchorBase::set_names(const pvector<std::string> names)
{
  // Clear existing names
  object_names = ObjectNames();

  // Parse and add new names
  if (names.empty()) {
    object_names.add_name(ObjectName::make_vernacular(""));
  } else {
    for (const auto &name : names) {
      object_names.add_name(ObjectNames::parse_name(name));
    }
  }
}

std::string
AnchorBase::get_friendly_name(void) const
{
  return object_names.get_friendly_name();
}

std::string
AnchorBase::get_name(void) const
{
  return object_names.get_name();
}

unsigned int
AnchorBase::get_num_names(void) const
{
  return object_names.get_num_names();
}

std::string
AnchorBase::get_name_at(unsigned int index) const
{
  return object_names.get_name_entry(index).get_full_name();
}

unsigned int
AnchorBase::get_num_source_names(void) const
{
  return object_names.get_source_names().size();
}

std::string
AnchorBase::get_source_name_at(unsigned int index) const
{
  pvector<std::string> source_names = object_names.get_source_names();
  return source_names[index];
}

std::string
AnchorBase::get_c_name(void) const
{
  return object_names.get_c_name();
}

std::string
AnchorBase::get_description(void) const
{
  return description;
}
