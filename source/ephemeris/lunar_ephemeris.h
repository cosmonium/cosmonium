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

#ifndef LUNAR_EPHEMERIS_H
#define LUNAR_EPHEMERIS_H

#include "orbits.h"
#include "type_utils.h"

class DourneauOrbit : public FunctionOrbit
{
PUBLISHED:
  DourneauOrbit(unsigned int planet_id,
          double average_period,
          double average_semi_major_axis,
          double average_eccentricity);

protected:
  DourneauOrbit(DourneauOrbit const &other);

PUBLISHED:
  virtual PT(OrbitBase) make_copy(void) const;

  virtual LPoint3d get_frame_position_at(double time);

  virtual LQuaterniond get_frame_rotation_at(double time);

protected:
  unsigned int planet_id;

  MAKE_TYPE("DourneauOrbit", FunctionOrbit);
};

class ELP82Orbit : public FunctionOrbit
{
PUBLISHED:
  ELP82Orbit(double average_period,
          double average_semi_major_axis,
          double average_eccentricity);

protected:
  ELP82Orbit(ELP82Orbit const &other);

PUBLISHED:
  virtual PT(OrbitBase) make_copy(void) const;

  virtual LPoint3d get_frame_position_at(double time);

  virtual LQuaterniond get_frame_rotation_at(double time);

  MAKE_TYPE("ELP82Orbit", FunctionOrbit);
};

class Gust86Orbit : public FunctionOrbit
{
PUBLISHED:
  Gust86Orbit(unsigned int planet_id,
          double average_period,
          double average_semi_major_axis,
          double average_eccentricity);

protected:
  Gust86Orbit(Gust86Orbit const &other);

PUBLISHED:
  virtual PT(OrbitBase) make_copy(void) const;

  virtual LPoint3d get_frame_position_at(double time);

  virtual LQuaterniond get_frame_rotation_at(double time);

protected:
  unsigned int planet_id;

  MAKE_TYPE("Gust86Orbit", FunctionOrbit);
};

class HTC20Orbit : public FunctionOrbit
{
PUBLISHED:
  HTC20Orbit(unsigned int planet_id,
          double average_period,
          double average_semi_major_axis,
          double average_eccentricity);

protected:
  HTC20Orbit(HTC20Orbit const &other);

PUBLISHED:
  virtual PT(OrbitBase) make_copy(void) const;

  virtual LPoint3d get_frame_position_at(double time);

  virtual LQuaterniond get_frame_rotation_at(double time);

protected:
  unsigned int planet_id;

  MAKE_TYPE("HTC20Orbit", FunctionOrbit);
};

class LieskeE5Orbit : public FunctionOrbit
{
PUBLISHED:
  LieskeE5Orbit(unsigned int planet_id,
          double average_period,
          double average_semi_major_axis,
          double average_eccentricity);

protected:
  LieskeE5Orbit(LieskeE5Orbit const &other);

PUBLISHED:
  virtual PT(OrbitBase) make_copy(void) const;

  virtual LPoint3d get_frame_position_at(double time);

  virtual LQuaterniond get_frame_rotation_at(double time);

protected:
  unsigned int planet_id;

  MAKE_TYPE("LieskeE5Orbit", FunctionOrbit);
};

class MeeusPlutoOrbit : public FunctionOrbit
{
PUBLISHED:
  MeeusPlutoOrbit(double average_period,
          double average_semi_major_axis,
          double average_eccentricity);

protected:
  MeeusPlutoOrbit(MeeusPlutoOrbit const &other);

PUBLISHED:
  virtual PT(OrbitBase) make_copy(void) const;

  virtual LPoint3d get_frame_position_at(double time);

  virtual LQuaterniond get_frame_rotation_at(double time);

  MAKE_TYPE("MeeusPlutoOrbit", FunctionOrbit);
};

class RckinOrbit : public FunctionOrbit
{
PUBLISHED:
  RckinOrbit(unsigned int planet_id,
          double average_period,
          double average_semi_major_axis,
          double average_eccentricity);

protected:
  RckinOrbit(RckinOrbit const &other);

PUBLISHED:
  virtual PT(OrbitBase) make_copy(void) const;

  virtual LPoint3d get_frame_position_at(double time);

  virtual LQuaterniond get_frame_rotation_at(double time);

protected:
  unsigned int planet_id;

  MAKE_TYPE("RckinOrbit", FunctionOrbit);
};

class VSOP87Orbit : public FunctionOrbit
{
PUBLISHED:
VSOP87Orbit(unsigned int planet_id,
          double average_period,
          double average_semi_major_axis,
          double average_eccentricity);

protected:
  VSOP87Orbit(VSOP87Orbit const &other);

PUBLISHED:
  virtual PT(OrbitBase) make_copy(void) const;

  virtual LPoint3d get_frame_position_at(double time);

  virtual LQuaterniond get_frame_rotation_at(double time);

protected:
  unsigned int planet_id;

  MAKE_TYPE("VSOP87Orbit", FunctionOrbit);
};

#endif
