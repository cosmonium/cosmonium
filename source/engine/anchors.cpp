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

#include "anchors.h"
#include "orbits.h"
#include "rotations.h"
#include "octreeNode.h"
#include "anchorTraverser.h"
#include "observer.h"
#include "infiniteFrustum.h"
#include "settings.h"
#include "astro.h"
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

AnchorBase::AnchorBase(unsigned int anchor_class, PyObject *ref_object, LColor point_color) :
  AnchorTreeBase(anchor_class),
  ref_object(ref_object),
  point_color(point_color),
  star(nullptr),
  //Flags
  visible(false),
  visibility_override(false),
  resolved(false),
  update_id(0),
  update_frozen(false),
  force_update(false),
  //Cached values
  _position(0.0),
  _global_position(0.0),
  _local_position(0.0),
  _orientation(LQuaterniond::ident_quat()),
  _equatorial(LQuaterniond::ident_quat()),
  _abs_magnitude(99.0),
  _app_magnitude(99.0),
  _extend(0.0),
  _height_under(0.0),
  _albedo(0.0),
  //Scene parameters
  support_offset_body_center(true),
  rel_position(0.0),
  distance_to_obs(0.0),
  vector_to_obs(0.0),
  distance_to_star(0.0),
  vector_to_star(0.0),
  visible_size(0.0),
  scene_position(0.0),
  scene_distance(0.0),
  scene_orientation(LQuaterniond::ident_quat()),
  scene_scale_factor(0.0)
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

LColor
AnchorBase::get_point_color(void)
{
  return point_color;
}

void
AnchorBase::set_point_color(LColor color)
{
  this->point_color = color;
}

AnchorBase *
AnchorBase::get_star(void)
{
  return star;
}

void
AnchorBase::set_star(AnchorBase *star)
{
  this->star = star;
}

void
AnchorBase::update_and_update_observer(double time, Observer &observer)
{
  update(time);
  update_observer(observer);
}

TypeHandle StellarAnchor::_type_handle;

StellarAnchor::StellarAnchor(unsigned int anchor_class,
    PyObject *ref_object,
    OrbitBase *orbit,
    RotationBase *rotation,
    LColor point_color) :
    AnchorBase(anchor_class, ref_object, point_color),
    orbit(orbit),
    rotation(rotation)
{
}

OrbitBase *
StellarAnchor::get_orbit(void)
{
  return orbit;
}

void
StellarAnchor::set_orbit(OrbitBase * orbit)
{
  this->orbit = orbit;
}

RotationBase *
StellarAnchor::get_rotation(void)
{
  return rotation;
}

void
StellarAnchor::set_rotation(RotationBase * rotation)
{
  this->rotation = rotation;
}

void
StellarAnchor::traverse(AnchorTraverser &visitor)
{
  visitor.traverse_anchor(this);
}

void
StellarAnchor::rebuild(void)
{
}
LPoint3d
StellarAnchor::get_absolute_reference_point(void)
{
  return _global_position;
}

LPoint3d
StellarAnchor::get_absolute_position(void)
{
  return _position;
}

LPoint3d
StellarAnchor::get_local_position(void)
{
  return _local_position;
}

double
StellarAnchor::get_position_bounding_radius(void)
{
  return orbit->get_bounding_radius();
}

LQuaterniond
StellarAnchor::get_absolute_orientation(void)
{
  return _orientation;
}

LQuaterniond
StellarAnchor::get_equatorial_rotation(void)
{
  return _equatorial;
}

LQuaterniond
StellarAnchor::get_sync_rotation(void)
{
  return _orientation;
}

double
StellarAnchor::get_absolute_magnitude(void)
{
  return _abs_magnitude;
}

void
StellarAnchor::set_absolute_magnitude(double magnitude)
{
  _abs_magnitude = magnitude;
}

double
StellarAnchor::get_apparent_magnitude(void)
{
  return _app_magnitude;
}

LPoint3d
StellarAnchor::calc_absolute_relative_position(AnchorBase *anchor)
{
    LPoint3d reference_point_delta = anchor->get_absolute_reference_point() - _global_position;
    LPoint3d local_delta = anchor->get_local_position() - _local_position;
    LPoint3d delta = reference_point_delta + local_delta;
    return delta;
}

void
StellarAnchor::update(double time)
{
  _orientation = rotation->get_absolute_rotation_at(time);
  _equatorial = rotation->get_equatorial_orientation_at(time);
  _local_position = orbit->get_local_position_at(time);
  _global_position = orbit->get_absolute_reference_point_at(time);
  _position = _global_position + _local_position;
}

LPoint3d
diff(LPoint3d a, LPoint3d b)
{
  return a - b;
}

void
StellarAnchor::update_observer(Observer &observer)
{
  //Use a function to do the diff, to work around a probable compiler bug
  LPoint3d reference_point_delta = diff(_global_position, observer.get_absolute_reference_point());
  LPoint3d local_delta = diff(_local_position, observer.get_local_position());
  rel_position = reference_point_delta + local_delta;
  distance_to_obs = rel_position.length();
  if (distance_to_obs > 0.0) {
      vector_to_obs = -rel_position / distance_to_obs;
      visible_size = _extend / (distance_to_obs * observer.pixel_size);
  } else {
      vector_to_obs = 0.0;
      visible_size = 0.0;
  }
  double radius = _extend;
  if (distance_to_obs > radius) {
      bool in_view = observer.rel_frustum->is_sphere_in(rel_position, radius);
      resolved = visible_size > settings.min_body_size;
      visible = in_view; // and (visible_size > 1.0 or _app_magnitude < settings.lowest_app_magnitude);
  } else {
      // We are in the object
      resolved = true;
      visible = true;
  }
}

double
StellarAnchor::get_luminosity(AnchorBase *star)
{
    LVector3d vector_to_star = calc_absolute_relative_position(star);
    double distance_to_star = vector_to_star.length();
    vector_to_star /= distance_to_star;
    double star_power = abs_mag_to_lum(star->get_absolute_magnitude());
    double area = 4 * M_PI * distance_to_star * distance_to_star * 1000 * 1000; // Units are in km
    if (area > 0.0) {
        double irradiance = star_power / area;
        double surface = M_PI * _extend * _extend * 1000 * 1000; // # Units are in km
        double received_energy = irradiance * surface;
        double reflected_energy = received_energy * _albedo;
        double phase_angle = vector_to_obs.dot(vector_to_star);
        double fraction = (1.0 + phase_angle) / 2.0;
        return reflected_energy * fraction;
    } else {
        std::cout << "No area\n";
        return 0.0;
    }
}

void
StellarAnchor::update_app_magnitude(AnchorBase *star)
{
  // TODO: Should be done by inheritance ?
  if (distance_to_obs == 0) {
    _app_magnitude = 99.0;
    return;
  }
  if ((content & Emissive) != 0) {
    _app_magnitude = abs_to_app_mag(_abs_magnitude, distance_to_obs);
  } else if ((content & Reflective) != 0) {
      if (star != 0) {
        double reflected = get_luminosity(star);
        _app_magnitude = abs_to_app_mag(lum_to_abs_mag(reflected), distance_to_obs);
        vector_to_star = star->get_local_position() - _local_position;
        distance_to_star = vector_to_star.length();
        vector_to_star /= distance_to_star;
      } else {
        _app_magnitude = 99.0;
      }
  } else {
    _app_magnitude = abs_to_app_mag(_abs_magnitude, distance_to_obs);
  }
  visible = visible && (visible_size > 1.0 || _app_magnitude < settings.lowest_app_magnitude);
}

void
StellarAnchor::calc_scene_params(Observer &observer, LPoint3d rel_position, LPoint3d abs_position, double distance_to_obs, LVector3d vector_to_obs)
{
    LPoint3d obj_position;
    if (settings.camera_at_origin) {
        obj_position = rel_position;
    } else {
        obj_position = abs_position;
    }
    distance_to_obs /= settings.scale;
    LPoint3d position;
    double distance;
    double scale_factor;
    if (!settings.use_depth_scaling || distance_to_obs <= observer.midPlane) {
        position = obj_position / settings.scale;
        distance = distance_to_obs;
        scale_factor = 1.0 / settings.scale;
    } else if (settings.use_inv_scaling) {
        LVector3d not_scaled = -vector_to_obs * observer.midPlane;
        double scaled_distance = observer.midPlane * (1 - observer.midPlane / distance_to_obs);
        LVector3d scaled = -vector_to_obs * scaled_distance;
        position = not_scaled + scaled;
        distance = observer.midPlane + scaled_distance;
        double ratio = distance / distance_to_obs;
        scale_factor = ratio / settings.scale;
    } else if (settings.use_log_scaling) {
        LVector3d not_scaled = -vector_to_obs * observer.midPlane;
        double scaled_distance = observer.midPlane * (1 - log2(observer.midPlane / distance_to_obs + 1));
        LVector3d scaled = -vector_to_obs * scaled_distance;
        position = not_scaled + scaled;
        distance = observer.midPlane + scaled_distance;
        double ratio = distance / distance_to_obs;
        scale_factor = ratio / settings.scale;
    }
    scene_position = position;
    scene_distance =  distance;
    scene_scale_factor = scale_factor;
}

void
StellarAnchor::update_scene(Observer &observer)
{
  LPoint3d scene_rel_position;
  double scene_rel_distance_to_obs;
  if (support_offset_body_center && visible && resolved && settings.offset_body_center) {
      scene_rel_position = rel_position + vector_to_obs * _height_under;
      scene_rel_distance_to_obs = distance_to_obs - _height_under;
  } else {
      scene_rel_position = rel_position;
      scene_rel_distance_to_obs = distance_to_obs;
  }
  calc_scene_params(observer, scene_rel_position, _local_position, scene_rel_distance_to_obs, vector_to_obs);
  scene_orientation = _orientation;
}

TypeHandle SystemAnchor::_type_handle;

SystemAnchor::SystemAnchor(PyObject *ref_object,
    OrbitBase *orbit,
    RotationBase *rotation,
    LColor point_color) :
    StellarAnchor(System, ref_object, orbit, rotation, point_color)
{
}

void
SystemAnchor::add_child(AnchorBase *child)
{
    children.push_back(child);
    child->parent = this;
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
  }
  child->parent = 0;
  if (!rebuild_needed) {
      set_rebuild_needed();
  }
}

void
SystemAnchor::traverse(AnchorTraverser &visitor)
{
  if (visitor.enter_system(this)) {
    visitor.traverse_system(this);
  }
}

void
SystemAnchor:: rebuild(void)
{
    content = System;
    _extend = 0;
    double luminosity = 0.0;
    for (auto child : children) {
        if (child->rebuild_needed) {
            child->rebuild();
        }
        content |= child->content;
        double position_bounding_radius = child->get_position_bounding_radius();
        if (child->_extend + position_bounding_radius > _extend) {
            _extend = child->_extend + position_bounding_radius;
        }
        //TODO: We need to handle the reflective case
        if ((child->content & Emissive) != 0) {
            luminosity += abs_mag_to_lum(child->_abs_magnitude);
        }
    }
    rebuild_needed = false;
    if (luminosity > 0.0) {
        _abs_magnitude = lum_to_abs_mag(luminosity);
    } else {
        _abs_magnitude = 99.0;
    }
}

TypeHandle OctreeAnchor::_type_handle;

OctreeAnchor::OctreeAnchor(PyObject *ref_object,
    OrbitBase *orbit,
    RotationBase *rotation,
    LColor point_color) :
    SystemAnchor(ref_object, orbit, rotation, point_color),
    recreate_octree(true)
{
  //TODO: Turn this into a parameter or infer it from the children
  _extend = 100000.0 * KmPerLy;
  //TODO: Should be configurable
  double top_level_absolute_magnitude = app_to_abs_mag(6.0, _extend * sqrt(3));
  //TODO: position should be extracted from orbit
  octree = new OctreeNode(0, /*this,*/ 0,
      LPoint3d(10 * KmPerLy, 10 * KmPerLy, 10 * KmPerLy),
      _extend,
      top_level_absolute_magnitude);
  octree->parent = this;
  //TODO: Should be done during rebuild
  _abs_magnitude = top_level_absolute_magnitude;
  //TODO: Right now an octree contains anything
  content = ~0;
  recreate_octree = true;
}

void
OctreeAnchor::traverse(AnchorTraverser &visitor)
{
  if (visitor.enter_octree_node(octree)) {
    octree->traverse(visitor);
  }
}

void
OctreeAnchor::rebuild(void)
{
  if (recreate_octree) {
    create_octree();
    recreate_octree = false;
  }
  if (octree->rebuild_needed) {
    octree->rebuild();
  }
  rebuild_needed = false;
}

void
OctreeAnchor::create_octree(void)
{
  for (auto child : children) {
    child->update(0);
    child->rebuild();
    octree->add(child);
  }
}

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
