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

#ifndef ANCHORS_H
#define ANCHORS_H

#include "referenceCount.h"
#include "pandabase.h"
#include "luse.h"
#include"type_utils.h"

class AnchorTraverser;
class CameraAnchor;
class OrbitBase;
class RotationBase;
class OctreeNode;

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
  AnchorBase(unsigned int anchor_class, PyObject *ref_object);

  virtual ~AnchorBase(void);

  PyObject *get_object(void) const;
  void set_body(PyObject *ref_object); //TODO: Is set needed ?
  MAKE_PROPERTY(body, get_object, set_body);

  virtual LPoint3d get_absolute_reference_point(void) = 0;

  virtual LPoint3d get_absolute_position(void) = 0;

  virtual LPoint3d get_local_position(void) = 0;

  virtual double get_position_bounding_radius(void) = 0;

  virtual LQuaterniond get_absolute_orientation(void) = 0;

  virtual LPoint3d calc_absolute_relative_position(AnchorBase *anchor);

  virtual LPoint3d calc_absolute_relative_position_to(LPoint3d position);

  virtual void update(double time, unsigned long int update_id) = 0;

  virtual void update_observer(CameraAnchor &observer, unsigned long int update_id) = 0;

  virtual void update_and_update_observer(double time, CameraAnchor &observer, unsigned long int update_id);

  INLINE double get_apparent_radius(void) { return get_position_bounding_radius(); }

  LPoint3d get_cached_absolute_position(void) const { return _global_position; }

  LPoint3d get_cached_local_position(void) { return _local_position; }

  LQuaterniond get_cached_absolute_orientation(void) {return _orientation; }

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
  double _extend;
  double _height_under;

  //Scene parameters
  //TODO: These should have getter
  LPoint3d rel_position;
  double distance_to_obs;
  LVector3d  vector_to_obs;
  double visible_size;
  double z_distance;

  MAKE_TYPE("AnchorBase", AnchorTreeBase);
};

LPoint3d diff(LPoint3d a, LPoint3d b);

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

  virtual void traverse(AnchorTraverser &visitor);

  virtual void rebuild(void);

  virtual LPoint3d get_absolute_reference_point(void);

  virtual LPoint3d get_absolute_position(void);

  virtual LPoint3d get_local_position(void);

  virtual double get_position_bounding_radius(void);

  virtual LQuaterniond get_absolute_orientation(void);

  virtual LQuaterniond get_equatorial_rotation(void);

  virtual LQuaterniond get_sync_rotation(void);

  virtual double get_absolute_magnitude(void);

  virtual void set_absolute_magnitude(double magnitude);

  virtual double get_apparent_magnitude(void);

  virtual LPoint3d calc_absolute_relative_position(AnchorBase *anchor);

  virtual void update(double time, unsigned long int update_id);

  virtual void update_observer(CameraAnchor &observer, unsigned long int update_id);

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

PUBLISHED:
  double _albedo;

public:
  LColor point_color;

protected:
  PT(OrbitBase) orbit;
  PT(RotationBase) rotation;

  MAKE_TYPE("StellarAnchor", AnchorBase);
};

class SystemAnchor : public StellarAnchor
{
PUBLISHED:
  SystemAnchor(PyObject *ref_object,
      OrbitBase *orbit,
      RotationBase *rotation,
      LColor point_color);

private:
  SystemAnchor(SystemAnchor const &other);
  void operator = (const SystemAnchor &other);

PUBLISHED:
  virtual void traverse(AnchorTraverser &visitor);
  virtual void update_app_magnitude(StellarAnchor *star = 0);
  virtual void rebuild(void);

  void add_child(StellarAnchor *child);
  void remove_child(StellarAnchor *child);

  void set_primary(StellarAnchor *primary);

public:
  std::vector<PT(StellarAnchor)> children;
  PT(StellarAnchor) primary;

  MAKE_TYPE("SystemAnchor", StellarAnchor);
};

class OctreeAnchor : public SystemAnchor
{
PUBLISHED:
  OctreeAnchor(PyObject *ref_object,
      OrbitBase *orbit,
      RotationBase *rotation,
      LColor point_color);

  virtual void traverse(AnchorTraverser &visitor);
  virtual void rebuild(void);

protected:
  void create_octree(void);

public:
  PT(OctreeNode) octree;
  bool recreate_octree;

  MAKE_TYPE("OctreeAnchor", SystemAnchor);
};

class UniverseAnchor : public OctreeAnchor
{
PUBLISHED:
  UniverseAnchor(PyObject *ref_object,
      OrbitBase *orbit,
      RotationBase *rotation,
      LColor point_color);
  virtual void traverse(AnchorTraverser &visitor);

  MAKE_TYPE("UniverseAnchor", OctreeAnchor);
};

#endif
