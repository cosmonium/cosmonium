/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2026 Laurent Deru.
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
#include "systemAnchor.h"

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
                       const vector_string &names) :
  AnchorTreeBase(anchor_class),
  ref_object(ref_object),
  //Flags
  visible(false),
  visibility_override(false),
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
  oid(-1),
  oid_color(0),
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
  // Scene anchor
  _scene_anchor(nullptr),
  // Owning system anchor
  _system(nullptr),
  // Name management
  description("")
{
  Py_INCREF(ref_object);

  // Parse and add names
  bool reflective = (anchor_class & AnchorClass::Reflective) != 0;
  if (names.empty()) {
    object_names.add_name(ObjectName::make_vernacular(""));
  } else {
    for (size_t i = 0; i < names.size(); ++i) {
      ObjectName parsed = ObjectNames::parse_name(names[i], reflective);
      object_names.add_name(parsed);
    }
  }
}

AnchorBase::AnchorBase(unsigned int anchor_class, PyObject *ref_object, LColor point_color,
                       PyObject *names) :
  AnchorTreeBase(anchor_class),
  ref_object(ref_object),
  //Flags
  visible(false),
  visibility_override(false),
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
  oid(-1),
  oid_color(0),
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
  // Scene anchor
  _scene_anchor(nullptr),
  // If this anchor is the primary body of a stellar system, this will point to the system anchor
  _system(nullptr),
  // Name management
  description("")
{
  Py_INCREF(ref_object);

  // Extract and parse names from Python list
  vector_string name_strings;
  if (names != nullptr) {
    if(PyList_Check(names)) {
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
    } else if (PyUnicode_Check(names)) {
      // If names is not a list, try to parse it as a single name
      const char *str;
      Py_ssize_t str_len;
      str = PyUnicode_AsUTF8AndSize(names, &str_len);
      if (str != nullptr) {
        name_strings.push_back(std::string(str, str_len));
      }
    }
  }

  // Parse and add names with originals
  bool reflective = (anchor_class & AnchorClass::Reflective) != 0;
  if (name_strings.empty()) {
    object_names.add_name(ObjectName::make_vernacular(""));
  } else {
    for (size_t i = 0; i < name_strings.size(); ++i) {
      ObjectName parsed = ObjectNames::parse_name(name_strings[i], reflective);
      object_names.add_name(parsed);
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

int
AnchorBase::get_oid(void) const
{
  return oid;
}

void
AnchorBase::set_oid(int oid)
{
  this->oid = oid;
}

LColor
AnchorBase::get_oid_color(void) const
{
  return oid_color;
}

void
AnchorBase::set_oid_color(LColor oid_color)
{
  this->oid_color = oid_color;
}

bool
AnchorBase::has_system(void) const
{
  return _system != nullptr;
}

SystemAnchor *
AnchorBase::get_system(void) const
{
  return _system;
}

void
AnchorBase::set_system(SystemAnchor * system)
{
  this->_system = system;
}

SceneAnchor *
AnchorBase::get_scene_anchor(void) const
{
  return _scene_anchor;
}

void
AnchorBase::set_scene_anchor(SceneAnchor *scene_anchor)
{
  _scene_anchor = scene_anchor;
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
void
AnchorBase::set_names(const vector_string &names)
{
  // Clear existing names
  object_names = ObjectNames();

  // Parse and add new names
  bool reflective = (content & AnchorClass::Reflective) != 0;
  if (names.empty()) {
    object_names.add_name(ObjectName::make_vernacular(""));
  } else {
    for (const auto &name : names) {
      object_names.add_name(ObjectNames::parse_name(name, reflective));
    }
  }
}

std::string
AnchorBase::get_name(void) const
{
  return object_names.get_name();
}

ObjectNames *
AnchorBase::get_names(void)
{
  return &object_names;
}

unsigned int
AnchorBase::get_num_source_names(void) const
{
  return object_names.get_source_names().size();
}

std::string
AnchorBase::get_source_name_at(unsigned int index) const
{
  vector_string source_names = object_names.get_source_names();
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

void
AnchorBase::set_description(const std::string &description)
{
  this->description = description;
}

bool
AnchorBase::is_system(void) const
{
  return false;
}

bool
AnchorBase::_is_named(const std::string &name_up) const
{
  // Check translated names
  vector_string all_names = object_names.get_all_names();
  for (const auto &n : all_names) {
    std::string n_up = n;
    std::transform(n_up.begin(), n_up.end(), n_up.begin(), ::toupper);
    if (n_up == name_up) return true;
  }
  // Check source (untranslated) names
  vector_string src_names = object_names.get_source_names();
  for (const auto &n : src_names) {
    std::string n_up = n;
    std::transform(n_up.begin(), n_up.end(), n_up.begin(), ::toupper);
    if (n_up == name_up) return true;
  }
  return false;
}

std::string
AnchorBase::_build_fullname(const std::string &name, const std::string &separator) const
{
  AnchorBase *parent_anchor = DCAST(AnchorBase, parent);
  if (parent_anchor == nullptr) {
    return name;
  }
  std::string parent_fullname;
  bool parent_primary_is_self = false;
  // Parent should always be a system, but check just in case
  if (parent_anchor->is_system()) {
    SystemAnchor *parent_system = DCAST(SystemAnchor, parent_anchor);
    if (parent_system != nullptr) {
      parent_primary_is_self = ((const AnchorBase *)parent_system->get_primary() == this);
    }
  }
  if (!parent_primary_is_self) {
    parent_fullname = parent_anchor->get_fullname(separator);
  } else {
    // We are the primary of the parent system, so skip it to avoid duplication in the name
    if (parent->parent != nullptr) {
      AnchorBase *pp = DCAST(AnchorBase, parent->parent);
      parent_fullname = pp ? pp->get_fullname(separator) : "";
    } else {
      parent_fullname = "";
    }
  }
  if (!parent_fullname.empty()) {
    return parent_fullname + separator + name;
  }
  return name;
}

std::string
AnchorBase::get_fullname(const std::string &separator) const
{
  return _build_fullname(get_c_name(), separator);
}
