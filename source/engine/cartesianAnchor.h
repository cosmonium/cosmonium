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

#ifndef CARTESIANANCHOR_H
#define CARTESIANANCHOR_H

#include "anchor.h"

class ReferenceFrame;
class StellarAnchor;

class CartesianAnchor : public AnchorBase
{
PUBLISHED:
  CartesianAnchor(unsigned int anchor_class, PyObject *ref_object, ReferenceFrame *frame, LColor point_color);
  CartesianAnchor(unsigned int anchor_class, PyObject *ref_object, ReferenceFrame *frame);
  virtual ~CartesianAnchor(void);

  virtual bool is_stellar(void) const;

  virtual bool has_orbit(void) const;

  virtual bool has_rotation(void) const;

  virtual bool has_frame(void) const;

  virtual double get_position_bounding_radius(void) const;

  virtual void traverse(AnchorTraverser &visitor);

  virtual void rebuild(void);

  void copy(CartesianAnchor const &other);

  ReferenceFrame *get_frame(void) const { return frame; }
  void set_frame(ReferenceFrame *frame);
  MAKE_PROPERTY(frame, get_frame, set_frame);

  virtual void do_update(void);

  void set_frame_position(LPoint3d position);

  virtual LPoint3d get_frame_position(void) const;

  void set_frame_orientation(LQuaterniond rotation);

  LQuaterniond get_frame_orientation(void) const;

  virtual LPoint3d get_local_position(void) const;

  void set_local_position(LPoint3d position);

  virtual LPoint3d get_absolute_reference_point(void) const;

  virtual void set_absolute_reference_point(LPoint3d new_reference_point);

  virtual LPoint3d get_absolute_position(void) const;

  void set_absolute_position(LPoint3d position);

  virtual LQuaterniond get_absolute_orientation(void) const;

  void set_absolute_orientation(LQuaterniond orientation);

  LPoint3d calc_absolute_position_of(LPoint3d frame_position);

  LPoint3d calc_relative_position_to(LPoint3d position);

  LPoint3d calc_frame_position_of_absolute(LPoint3d position);

  LPoint3d calc_frame_position_of_local(LPoint3d position);

  LQuaterniond calc_frame_orientation_of(LQuaterniond orientation);

  LPoint3d calc_local_position_of_frame(LPoint3d position);

  virtual void update(double time, unsigned long int update_id);

  virtual void update_observer(CameraAnchor &observer, unsigned long int update_id);

  virtual void update_state(CameraAnchor &observer, unsigned long int update_id);

  //Temporary
  virtual void update_luminosity(StellarAnchor *star = 0);

protected:
  PT(ReferenceFrame) frame;
  LPoint3d _frame_position;
  LQuaterniond _frame_orientation;

  MAKE_TYPE("CartesianAnchor", AnchorBase);
};


class OriginAnchor : public CartesianAnchor
{
PUBLISHED:
  OriginAnchor(unsigned int anchor_class, PyObject *ref_object);

protected:
  MAKE_TYPE("OriginAnchor", CartesianAnchor);
};


class FlatSurfaceAnchor : public OriginAnchor
{
PUBLISHED:
  FlatSurfaceAnchor(unsigned int anchor_class, PyObject *ref_object, PyObject *ref_surface);
  virtual ~FlatSurfaceAnchor(void);

  void set_surface(PyObject *ref_surface);

  virtual void update_observer(CameraAnchor &observer, unsigned long int update_id);
  virtual void update_state(CameraAnchor &observer, unsigned long int update_id);

private:
  PyObject *ref_surface;

protected:
  MAKE_TYPE("FlatSurfaceAnchor", OriginAnchor);
};


class ObserverAnchor : public CartesianAnchor
{
PUBLISHED:
  ObserverAnchor(unsigned int anchor_class, PyObject *ref_object);

  virtual void update(double time, unsigned long int update_id);

  virtual void update_observer(CameraAnchor &observer, unsigned long int update_id);
  virtual void update_state(CameraAnchor &observer, unsigned long int update_id);

protected:
  MAKE_TYPE("ObserverAnchor", CartesianAnchor);
};

#endif //CARTESIANANCHORS_H
