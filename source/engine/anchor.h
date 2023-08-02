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

#ifndef ANCHOR_H
#define ANCHOR_H

#include "referenceCount.h"
#include "pandabase.h"
#include "luse.h"
#include"type_utils.h"

class AnchorTraverser;
class CameraAnchor;

class AnchorTreeBase : public TypedObject, public ReferenceCount
{
public:
  AnchorTreeBase(unsigned int anchor_class);
  virtual ~AnchorTreeBase(void);

  AnchorTreeBase *get_parent(void);
  void set_parent(AnchorTreeBase *parent);
  MAKE_PROPERTY(parent, get_parent, set_parent); //TODO: keep set parent ?

  virtual void set_rebuild_needed(void);

  virtual void rebuild(void) = 0;

  virtual void traverse(AnchorTraverser &visitor) = 0;

PUBLISHED:
  int content;
  bool rebuild_needed;

public:
  PT(AnchorTreeBase) parent;

  MAKE_TYPE_2("AnchorTreeBase", TypedObject, ReferenceCount);
};


class AnchorBase : public AnchorTreeBase
{
PUBLISHED:
  enum AnchorClass {
    Emissive   = 1,
    Reflective = 2,
    System = 4
  };
  AnchorBase(unsigned int anchor_class, PyObject *ref_object, LColor point_color);

  virtual ~AnchorBase(void);

  PyObject *get_object(void) const;
  void set_body(PyObject *ref_object); //TODO: Is set needed ?
  MAKE_PROPERTY(body, get_object, set_body);

  LColor get_point_color(void);
  void set_point_color(LColor color);
  MAKE_PROPERTY(point_color, get_point_color, set_point_color);

  virtual bool is_stellar(void) const = 0;

  virtual bool has_orbit(void) const = 0;

  virtual bool has_rotation(void) const = 0;

  virtual bool has_frame(void) const = 0;

  double get_bounding_radius(void);

  void set_bounding_radius(double bounding_radius);

  virtual double get_position_bounding_radius(void) = 0;

  virtual LPoint3d get_absolute_reference_point(void) = 0;

  virtual LPoint3d get_absolute_position(void) = 0;

  virtual LPoint3d get_local_position(void) = 0;

  virtual LQuaterniond get_absolute_orientation(void) = 0;

  virtual LPoint3d calc_absolute_relative_position(AnchorBase *anchor);

  virtual LPoint3d calc_absolute_relative_position_to(LPoint3d position);

  virtual void update(double time, unsigned long int update_id) = 0;

  virtual void update_observer(CameraAnchor &observer, unsigned long int update_id) = 0;

  virtual void update_state(CameraAnchor &observer, unsigned long int update_id) = 0;

  virtual void update_all(double time, CameraAnchor &observer, unsigned long int update_id);

  INLINE double get_apparent_radius(void) { return get_bounding_radius(); }

  LPoint3d get_cached_absolute_position(void) const { return _global_position; }

  LPoint3d get_cached_local_position(void) { return _local_position; }

  LQuaterniond get_cached_absolute_orientation(void) {return _orientation; }

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
  PyObject *ref_object;

PUBLISHED:
  //Flags
  bool was_visible;
  bool visible;
  bool visibility_override;
  bool was_resolved;
  bool resolved;
  unsigned long int update_id;
  bool update_frozen;
  bool force_update;

public:
  //Cached values
  LPoint3d _global_position;
  LPoint3d _local_position;

PUBLISHED:
  //TODO: These should have getter and setter
  LPoint3d _position;
  LQuaterniond _orientation;
  double _height_under;

  //Scene parameters
  //TODO: These should have getter
  LPoint3d rel_position;
  double distance_to_obs;
  LVector3d  vector_to_obs;
  double visible_size;
  double z_distance;

protected:
  double bounding_radius;

public:
  // Temporary
  LColor point_color;
  double _albedo;
  double _intrinsic_luminosity;
  double _reflected_luminosity;
  double _point_radiance;

  MAKE_TYPE("AnchorBase", AnchorTreeBase);
};

#include "anchor.I"

#endif
