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

  virtual bool is_stellar(void) const;

  virtual bool has_orbit(void) const;

  virtual bool has_rotation(void) const;

  virtual bool has_frame(void) const;

  OrbitBase *get_orbit(void) const;
  void set_orbit(OrbitBase * orbit);
  MAKE_PROPERTY(orbit, get_orbit, set_orbit);

  RotationBase *get_rotation(void) const;
  void set_rotation(RotationBase * rotation);
  MAKE_PROPERTY(rotation, get_rotation, set_rotation);

  virtual double get_position_bounding_radius(void) const;

  virtual void traverse(AnchorTraverser &visitor);

  virtual void rebuild(void);

  virtual LPoint3d get_absolute_reference_point(void) const;

  virtual LPoint3d get_absolute_position(void) const;

  virtual LPoint3d get_local_position(void) const;

  virtual LPoint3d get_frame_position(void) const;

  virtual LQuaterniond get_absolute_orientation(void) const;

  virtual LQuaterniond get_equatorial_rotation(void) const;

  virtual LQuaterniond get_sync_rotation(void) const;

  virtual double get_absolute_magnitude(void) const;

  virtual double get_apparent_magnitude(void) const;

  virtual LPoint3d calc_absolute_relative_position(AnchorBase *anchor) const;

  virtual void update(double time, unsigned long int update_id);

  virtual void update_observer(CameraAnchor &observer, unsigned long int update_id);

  virtual void update_state(CameraAnchor &observer, unsigned long int update_id);

  virtual void update_luminosity(StellarAnchor *star = 0);

public:
  double get_reflected_luminosity(StellarAnchor *star) const;

public:
  LQuaterniond _equatorial;

protected:
  PT(OrbitBase) orbit;
  PT(RotationBase) rotation;

  MAKE_TYPE("StellarAnchor", AnchorBase);
};

#endif
