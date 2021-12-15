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

#include "systemAnchor.h"
#include "anchorTraverser.h"
#include "astro.h"

TypeHandle SystemAnchor::_type_handle;

SystemAnchor::SystemAnchor(PyObject *ref_object,
    OrbitBase *orbit,
    RotationBase *rotation,
    LColor point_color) :
    StellarAnchor(System, ref_object, orbit, rotation, point_color),
    primary(nullptr)
{
}

void
SystemAnchor::add_child(StellarAnchor *child)
{
    children.push_back(child);
    child->parent = this;
    if (!rebuild_needed) {
        set_rebuild_needed();
    }
}

void
SystemAnchor::remove_child(StellarAnchor *child)
{
  auto it = std::find(children.begin(), children.end(), child);
  if (it != children.end()) {
      children.erase(it);
  }
  child->parent = 0;
  if (!rebuild_needed) {
      set_rebuild_needed();
  }
}

void
SystemAnchor::set_primary(StellarAnchor *primary)
{
  this->primary = primary;
}

void
SystemAnchor::traverse(AnchorTraverser &visitor)
{
  if (visitor.enter_system(this)) {
    visitor.traverse_system(this);
  }
}

void
SystemAnchor::update_app_magnitude(StellarAnchor *star)
{
  if (primary != nullptr) {
    primary->update_app_magnitude(star);
    _abs_magnitude = primary->_abs_magnitude;
    _app_magnitude = primary->_app_magnitude;
  } else {
    StellarAnchor::update_app_magnitude(star);
  }
}

void
SystemAnchor:: rebuild(void)
{
    content = System;
    _extend = 0;
    for (auto child : children) {
        if (child->rebuild_needed) {
            child->rebuild();
        }
        content |= child->content;
        double position_bounding_radius = child->get_position_bounding_radius();
        if (child->_extend + position_bounding_radius > _extend) {
            _extend = child->_extend + position_bounding_radius;
        }
    }
    if (primary == nullptr) {
      double luminosity = 0.0;
      for (auto child : children) {
          //TODO: We need to handle the reflective case
          if ((child->content & Emissive) != 0) {
              luminosity += abs_mag_to_lum(child->_abs_magnitude);
          }
      }
      if (luminosity > 0.0) {
          _abs_magnitude = lum_to_abs_mag(luminosity);
      } else {
          _abs_magnitude = 1000.0;
      }
    } else {
      _abs_magnitude = primary->_abs_magnitude;
    }
    rebuild_needed = false;
}
