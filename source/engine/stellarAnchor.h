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

#ifndef STELLARANCHOR_H
#define STELLARANCHOR_H

#include"anchor.h"

class OrbitBase;
class RotationBase;

class StellarAnchor : public AnchorBase
{
PUBLISHED:
  StellarAnchor(unsigned int anchor_class,
      PyObject *ref_object,
      OrbitBase *orbit,
      RotationBase *rotation,
      LColor point_color);
  virtual ~StellarAnchor(void);

  OrbitBase *get_orbit(void);
  void set_orbit(OrbitBase * orbit);
  MAKE_PROPERTY(orbit, get_orbit, set_orbit);

  RotationBase *get_rotation(void);
  void set_rotation(RotationBase * rotation);
  MAKE_PROPERTY(rotation, get_rotation, set_rotation);

  LColor get_point_color(void);
  void set_point_color(LColor color);
  MAKE_PROPERTY(point_color, get_point_color, set_point_color);

  virtual double get_position_bounding_radius(void);

  virtual void traverse(AnchorTraverser &visitor);

  virtual void rebuild(void);

  virtual LPoint3d get_absolute_reference_point(void);

  virtual LPoint3d get_absolute_position(void);

  virtual LPoint3d get_local_position(void);

  virtual LQuaterniond get_absolute_orientation(void);

  virtual LQuaterniond get_equatorial_rotation(void);

  virtual LQuaterniond get_sync_rotation(void);

  virtual double get_absolute_magnitude(void);

  virtual double get_apparent_magnitude(void);

  virtual double get_radiant_flux(void);

  virtual double get_point_radiance(double distance);

  virtual LPoint3d calc_absolute_relative_position(AnchorBase *anchor);

  virtual void update(double time, unsigned long int update_id);

  virtual void update_observer(CameraAnchor &observer, unsigned long int update_id);

  virtual void update_state(CameraAnchor &observer, unsigned long int update_id);

  virtual void update_luminosity(StellarAnchor *star = 0);

  INLINE double get_albedo(void) const;
  INLINE void set_albedo(double albedo);
  MAKE_PROPERTY(_albedo, get_albedo, set_albedo);

  INLINE double get_intrinsic_luminosity(void) const;
  INLINE void set_intrinsic_luminosity(double intrinsic_luminosity);
  MAKE_PROPERTY(_intrinsic_luminosity, get_intrinsic_luminosity, set_intrinsic_luminosity);

  INLINE double get_reflected_luminosity(void) const;
  MAKE_PROPERTY(_reflected_luminosity, get_reflected_luminosity);

  INLINE double get_point_radiance(void) const;
  MAKE_PROPERTY(_point_radiance, get_point_radiance);

public:
  double get_reflected_luminosity(StellarAnchor *star);

public:
  LQuaterniond _equatorial;
  double _albedo;
  double _intrinsic_luminosity;
  double _reflected_luminosity;
  double _point_radiance;

public:
  LColor point_color;

protected:
  PT(OrbitBase) orbit;
  PT(RotationBase) rotation;

  MAKE_TYPE("StellarAnchor", AnchorBase);
};

#include "stellarAnchor.I"

#endif
