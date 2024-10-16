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
    AnchorBase(anchor_class, ref_object, point_color),
    orbit(orbit),
    rotation(rotation),
    _equatorial(LQuaterniond::ident_quat())
{
}

StellarAnchor::~StellarAnchor(void)
{
}

bool
StellarAnchor::is_stellar(void) const
{
    return true;
}

bool
StellarAnchor::has_orbit(void) const
{
    return true;
}

bool
StellarAnchor::has_rotation(void) const
{
    return true;
}

bool
StellarAnchor::has_frame(void) const
{
    return false;
}

OrbitBase *
StellarAnchor::get_orbit(void) const
{
  return orbit;
}

void
StellarAnchor::set_orbit(OrbitBase * orbit)
{
  this->orbit = orbit;
}

RotationBase *
StellarAnchor::get_rotation(void) const
{
  return rotation;
}

void
StellarAnchor::set_rotation(RotationBase * rotation)
{
  this->rotation = rotation;
}

double
StellarAnchor::get_position_bounding_radius(void) const
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
StellarAnchor::get_absolute_reference_point(void) const
{
  return _global_position;
}

LPoint3d
StellarAnchor::get_absolute_position(void) const
{
  return _position;
}

LPoint3d
StellarAnchor::get_local_position(void) const
{
  return _local_position;
}

LPoint3d
StellarAnchor::get_frame_position(void) const
{
    return orbit->get_frame()->get_frame_position(_local_position);
}

LQuaterniond
StellarAnchor::get_absolute_orientation(void) const
{
  return _orientation;
}

LQuaterniond
StellarAnchor::get_equatorial_rotation(void) const
{
  return _equatorial;
}

LQuaterniond
StellarAnchor::get_sync_rotation(void) const
{
  return _orientation;
}


double
StellarAnchor::get_absolute_magnitude(void) const
{
  return lum_to_abs_mag(get_radiant_flux() / L0);
}


double
StellarAnchor::get_apparent_magnitude(void) const
{
  return abs_to_app_mag(get_absolute_magnitude(), distance_to_obs);
}


LPoint3d
StellarAnchor::calc_absolute_relative_position(AnchorBase *anchor) const
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
StellarAnchor::get_reflected_luminosity(StellarAnchor *star) const
{
    LVector3d vector_to_star = calc_absolute_relative_position(star);
    double distance_to_star = vector_to_star.length();
    vector_to_star /= distance_to_star;
    if (distance_to_star > 0.0) {
        double irradiance = star->get_point_radiance(distance_to_star);
        double surface = M_PI * bounding_radius * bounding_radius * 1000 * 1000; // # Units are in km
        double received_power = irradiance * surface;
        double reflected_power = received_power * _albedo;
        double phase_angle = vector_to_obs.dot(vector_to_star);
        double fraction = (1.0 + phase_angle) / 2.0;
        return reflected_power * fraction;
    } else {
        return 0.0;
    }
}

void
StellarAnchor::update_luminosity(StellarAnchor *star)
{
  if ((content & Reflective) != 0) {
      if (star != 0) {
        _reflected_luminosity = get_reflected_luminosity(star);
      } else {
        _reflected_luminosity = 0.0;
      }
  } else {
    _reflected_luminosity = 0.0;
  }
  if (distance_to_obs > 0) {
    _point_radiance = get_point_radiance(distance_to_obs);
  } else {

  }
}
