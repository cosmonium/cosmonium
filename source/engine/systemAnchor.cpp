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

#include "systemAnchor.h"
#include "anchorTraverser.h"
#include "astro.h"
#include "py_panda.h"
#include <algorithm>
#include <sstream>

TypeHandle SystemAnchor::_type_handle;

SystemAnchor::SystemAnchor(PyObject *ref_object,
    OrbitBase *orbit,
    RotationBase *rotation,
    LColor point_color,
    const pvector<std::string> names,
    const pvector<std::string> source_names,
    const std::string &description) :
    StellarAnchor(System, ref_object, orbit, rotation, point_color, names, source_names, description),
    _primary(nullptr),
    _star_system(false)
{
}

SystemAnchor::SystemAnchor(PyObject *ref_object,
    OrbitBase *orbit,
    RotationBase *rotation,
    LColor point_color,
    PyObject *names,
    PyObject *source_names,
    const std::string &description) :
    StellarAnchor(System, ref_object, orbit, rotation, point_color, names, source_names, description),
    _primary(nullptr),
    _star_system(false)
{
}

bool
SystemAnchor::is_system(void) const
{
  return true;
}

std::string
SystemAnchor::get_fullname(const std::string &separator) const
{
  std::string name;
  if (_primary != nullptr) {
    name = _primary->get_c_name();
  } else {
    name = get_c_name();
  }
  return _build_fullname(name, separator);
}

SystemAnchor *
SystemAnchor::get_or_create_system(void)
{
  // A SystemAnchor is already a stellar system — return itself.
  return this;
}

void
SystemAnchor::add_child(AnchorBase *child)
{
    children.push_back(child);
    child->parent = this;
    // Register all names in the fast-lookup map
    pvector<std::string> all_names = child->_get_names();
    for (const auto &n : all_names) {
        std::string key = n;
        std::transform(key.begin(), key.end(), key.begin(), ::toupper);
        children_map[key] = child;
    }
    if (!rebuild_needed) {
        set_rebuild_needed();
    }
}

void
SystemAnchor::remove_child(AnchorBase *child)
{
  auto it = std::find(children.begin(), children.end(), child);
  if (it != children.end()) {
      children.erase(it);
      child->parent = nullptr;
      // Remove all name entries from the fast-lookup map
      pvector<std::string> all_names = child->_get_names();
      for (const auto &n : all_names) {
          std::string key = n;
          std::transform(key.begin(), key.end(), key.begin(), ::toupper);
          children_map.erase(key);
      }
  }
  if (!rebuild_needed) {
      set_rebuild_needed();
  }
}

unsigned int
SystemAnchor::get_num_children(void) const
{
  return (unsigned int)children.size();
}

AnchorBase *
SystemAnchor::get_child_at(unsigned int index) const
{
  if (index < children.size()) {
      return children[index];
  }
  return nullptr;
}

StellarAnchor *
SystemAnchor::get_primary(void) const
{
  return _primary;
}

void
SystemAnchor::set_primary(StellarAnchor *primary)
{
  this->_primary = primary;
  if (primary != nullptr) {
    primary->set_system(this);
  }
}

void
SystemAnchor::set_star_system(bool star_system)
{
  this->_star_system = star_system;
}

bool
SystemAnchor::get_star_system(void) const
{
  return _star_system;
}

void
SystemAnchor::traverse(AnchorTraverser &visitor)
{
  if (visitor.enter_system(this)) {
    visitor.traverse_system(this);
  }
}

void
SystemAnchor::update_luminosity(StellarAnchor *star)
{
  if (_primary != nullptr) {
    _primary->update_luminosity(star);
    _intrinsic_luminosity = _primary->_intrinsic_luminosity;
    _reflected_luminosity = _primary->_reflected_luminosity;
    _point_radiance = _primary->_point_radiance;
  } else {
    StellarAnchor::update_luminosity(star);
  }
}

void
SystemAnchor:: rebuild(void)
{
    content = System;
    bounding_radius = 0;
    for (auto child : children) {
        if (child->rebuild_needed) {
            child->rebuild();
        }
        content |= child->content;
        double farthest_distance = child->get_position_bounding_radius() + child->get_bounding_radius();
        if (farthest_distance > bounding_radius) {
          bounding_radius = farthest_distance;
        }
    }
    if (_primary == nullptr) {
      double luminosity = 0.0;
      for (auto child : children) {
          //TODO: We need to handle the reflective case
          if ((child->content & Emissive) != 0) {
              luminosity += child->_intrinsic_luminosity;
          }
      }
      _intrinsic_luminosity = luminosity;
    } else {
      _intrinsic_luminosity = _primary->_intrinsic_luminosity;
    }
    rebuild_needed = false;
}

AnchorBase *
SystemAnchor::find_child_by_name(const std::string &name) const
{
    // Fast path via children_map
    std::string name_up = name;
    std::transform(name_up.begin(), name_up.end(), name_up.begin(), ::toupper);
    auto it = children_map.find(name_up);
    if (it != children_map.end()) {
        return it->second;
    }
    // Fallback to find simple system
    for (const auto &child : children) {
        // SimpleSystem-like: child is a system with a primary whose name matches
        if (child->is_system()) {
            SystemAnchor *sub = DCAST(SystemAnchor, child);
            StellarAnchor *primary = sub->get_primary();
            if (primary != nullptr && primary->_is_named(name_up)) {
                return primary;
            }
        }
    }
    return nullptr;
}

AnchorBase *
SystemAnchor::find_nth_child(int index) const
{
    if (index >= 0 && (size_t)index < children.size()) {
        return children[index];
    }
    return nullptr;
}

// Helper: split a std::string by a single separator character
static std::vector<std::string>
split_path(const std::string &s, char sep)
{
    std::vector<std::string> parts;
    std::istringstream ss(s);
    std::string token;
    while (std::getline(ss, token, sep)) {
        parts.push_back(token);
    }
    return parts;
}

AnchorBase *
SystemAnchor::find_by_path(const std::vector<std::string> &parts) const
{
    if (parts.empty()) {
      return nullptr;
    }

    // Resolve the first component against direct children
    AnchorBase *child = find_child_by_name(parts[0]);
    if (child == nullptr) {
        return nullptr;
    }

    // No sub-path: return the child if conditions are met
    if (parts.size() == 1) {
        return child;
    }

    std::vector<std::string> sub_parts(parts.begin() + 1, parts.end());

    // Recurse: go through child's anchor (system) or child's containing system anchor
    AnchorBase *result = nullptr;
    if (child->is_system()) {
        SystemAnchor *sub = DCAST(SystemAnchor, child);
        result = sub->find_by_path(sub_parts);
    } else if (child->get_system() != nullptr) {
        SystemAnchor *sub = child->get_system();
        result = sub->find_by_path(sub_parts);
    }

    return result;
}

AnchorBase *
SystemAnchor::find_by_path(const std::string &path, const std::string &separator) const
{
    // Build the list of name components
    std::vector<std::string> parts;
    parts = split_path(path, separator.empty() ? '/' : separator[0]);

    return find_by_path(parts);
}

AnchorBase *
SystemAnchor::find_by_path(PyObject *path_obj, const std::string &separator) const
{
  // Build the list of name components
  std::vector<std::string> parts;
  if (PyList_Check(path_obj)) {
      Py_ssize_t n = PyList_Size(path_obj);
      for (Py_ssize_t i = 0; i < n; i++) {
          PyObject *item = PyList_GetItem(path_obj, i);
          if (item && PyUnicode_Check(item)) {
              parts.push_back(PyUnicode_AsUTF8(item));
          }
      }
  } else if (PyUnicode_Check(path_obj)) {
      const char *s = PyUnicode_AsUTF8(path_obj);
      if (s) {
          parts = split_path(s, separator.empty() ? '/' : separator[0]);
      }
  }
  return find_by_path(parts);
}
