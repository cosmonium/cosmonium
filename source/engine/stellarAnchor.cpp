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

#include "stellarAnchor.h"
#include "cameraAnchor.h"
#include "orbits.h"
#include "rotations.h"
#include "anchorTraverser.h"
#include "infiniteFrustum.h"
#include "settings.h"
#include "astro.h"


TypeHandle StellarAnchor::_type_handle;

StellarAnchor::StellarAnchor(unsigned int anchor_class,
    PyObject *ref_object,
    OrbitBase *orbit,
    RotationBase *rotation,
    LColor point_color) :
    AnchorBase(anchor_class, ref_object),
    orbit(orbit),
    rotation(rotation),
    point_color(point_color),
    _equatorial(LQuaterniond::ident_quat()),
    _abs_magnitude(1000.0),
    _app_magnitude(1000.0),
    _albedo(0.0)
{
}

StellarAnchor::~StellarAnchor(void)
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

LColor
StellarAnchor::get_point_color(void)
{
  return point_color;
}

void
StellarAnchor::set_point_color(LColor color)
{
  this->point_color = color;
}

double
StellarAnchor::get_position_bounding_radius(void)
{
  return orbit->get_bounding_radius();
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
StellarAnchor::update(double time, unsigned long int update_id)
{
  if (update_id == this->update_id) return;
  _orientation = rotation->get_absolute_rotation_at(time);
  _equatorial = rotation->get_equatorial_orientation_at(time);
  _local_position = orbit->get_local_position_at(time);
  _global_position = orbit->get_absolute_reference_point_at(time);
  _position = _global_position + _local_position;
}

void
StellarAnchor::update_observer(CameraAnchor &observer, unsigned long int update_id)
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
StellarAnchor::update_state(CameraAnchor &observer, unsigned long int update_id)
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


double
StellarAnchor::get_luminosity(StellarAnchor *star)
{
    LVector3d vector_to_star = calc_absolute_relative_position(star);
    double distance_to_star = vector_to_star.length();
    vector_to_star /= distance_to_star;
    double star_power = abs_mag_to_lum(star->get_absolute_magnitude());
    double area = 4 * M_PI * distance_to_star * distance_to_star * 1000 * 1000; // Units are in km
    if (area > 0.0) {
        double irradiance = star_power / area;
        double surface = M_PI * bounding_radius * bounding_radius * 1000 * 1000; // # Units are in km
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
StellarAnchor::update_app_magnitude(StellarAnchor *star)
{
  // TODO: Should be done by inheritance ?
  if (distance_to_obs == 0) {
    _app_magnitude = 1000.0;
    return;
  }
  if ((content & Emissive) != 0) {
    _app_magnitude = abs_to_app_mag(_abs_magnitude, distance_to_obs);
  } else if ((content & Reflective) != 0) {
      if (star != 0) {
        double reflected = get_luminosity(star);
        if (reflected > 0.0) {
          _app_magnitude = abs_to_app_mag(lum_to_abs_mag(reflected), distance_to_obs);
        } else {
          _app_magnitude = 1000.0;
        }
      } else {
        _app_magnitude = 1000.0;
      }
  } else {
    _app_magnitude = abs_to_app_mag(_abs_magnitude, distance_to_obs);
  }
}
