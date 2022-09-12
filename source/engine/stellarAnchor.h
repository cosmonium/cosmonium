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

  virtual void set_absolute_magnitude(double magnitude);

  virtual double get_apparent_magnitude(void);

  virtual double get_radiant_flux(void);

  virtual double get_radiant_intensity(void);

  virtual double get_radiance(void);

  virtual double get_irradiance(void);

  virtual double get_point_radiance(void);

  virtual double get_point_irradiance(void);

  virtual LPoint3d calc_absolute_relative_position(AnchorBase *anchor);

  virtual void update(double time, unsigned long int update_id);

  virtual void update_observer(CameraAnchor &observer, unsigned long int update_id);

  virtual void update_state(CameraAnchor &observer, unsigned long int update_id);

  virtual void update_app_magnitude(StellarAnchor *star = 0);

  //TODO: Temporary until Python code is aligned
  MAKE_PROPERTY(_abs_magnitude, get_absolute_magnitude, set_absolute_magnitude);
  MAKE_PROPERTY(_app_magnitude, get_apparent_magnitude);

public:
  double get_luminosity(StellarAnchor *star);

public:
  LQuaterniond _equatorial;
  double _abs_magnitude;
  double _app_magnitude;
  double reflected;

PUBLISHED:
  double _albedo;

public:
  LColor point_color;

protected:
  PT(OrbitBase) orbit;
  PT(RotationBase) rotation;

  MAKE_TYPE("StellarAnchor", AnchorBase);
};

#endif
