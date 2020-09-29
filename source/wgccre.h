/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2020 Laurent Deru.
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

#ifndef WGCCRE_H
#define WGCCRE_H

#include "pandabase.h"
#include "luse.h"

class RotationBase
{
PUBLISHED:
  virtual ~RotationBase(void);
  virtual LQuaterniond get_frame_equatorial_orientation_at(double time) = 0;
  virtual LQuaterniond get_frame_rotation_at(double time) = 0;
  virtual bool is_flipped(void) const;

public:
  LQuaterniond calc_orientation(double a, double d, bool flipped=false) const;
};

class CachedRotationBase: public RotationBase
{
PUBLISHED:
  CachedRotationBase(void);
  virtual LQuaterniond get_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond get_frame_rotation_at(double time);

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time) = 0;
  virtual LQuaterniond calc_frame_rotation_at(double time) = 0;

private:
  double last_orientation_time;
  LQuaterniond last_orientation;
  double last_rotation_time;
  LQuaterniond last_rotation;
};

class WGCCRESimpleRotation: public RotationBase
{
PUBLISHED:
  WGCCRESimpleRotation(double a0, double d0, double meridian_angle,
      double mean_motion, double epoch);

  virtual LQuaterniond get_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond get_frame_rotation_at(double time);
  virtual bool is_flipped(void) const;

private:
  LQuaterniond orientation;
  double meridian_angle;
  double mean_motion;
  bool flipped;
  double epoch;
};

class WGCCRESimplePrecessingRotation: public RotationBase
{
PUBLISHED:
  WGCCRESimplePrecessingRotation(double a0, double a0_rate, double d0,
      double d0_rate, double meridian_angle, double mean_motion, double epoch);

  virtual LQuaterniond get_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond get_frame_rotation_at(double time);
  virtual bool is_flipped(void) const;

private:
  double a0;
  double a0_rate;
  double d0;
  double d0_rate;
  double meridian_angle;
  double mean_motion;
  bool flipped;
  double epoch;
};

// ############################################################################
// Planets
// ############################################################################

class WGCCREMercuryRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCREMercuryRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREMarsRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCREMarsRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREJupiterRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCREJupiterRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCRENeptuneRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCRENeptuneRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

// ############################################################################
// Moon
// ############################################################################

class WGCCRE9MoonRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCRE9MoonRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

// ############################################################################
// Mars moons
// ############################################################################

class WGCCREPhobosRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCREPhobosRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREDeimosRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCREDeimosRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

// ############################################################################
// Jupiter moons
// ############################################################################

class WGCCREAmaltheaRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCREAmaltheaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREThebeRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCREThebeRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREIoRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCREIoRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREEuropaRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCREEuropaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREGanymedeRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCREGanymedeRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCRECallistoRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCRECallistoRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

// ############################################################################
// Saturn moons
// ############################################################################

class WGCCREEpimetheusRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCREEpimetheusRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREJanusRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCREJanusRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREMimasRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCREMimasRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCRETethysRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCRETethysRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCRERheaRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCRERheaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

// ############################################################################
// Uranus moons
// ############################################################################

class WGCCRECordeliaRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCRECordeliaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREOpheliaRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCREOpheliaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREBiancaRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCREBiancaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCRECressidaRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCRECressidaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREDesdemonaRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCREDesdemonaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREJulietRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCREJulietRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREPortiaRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCREPortiaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCRERosalindRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCRERosalindRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREBelindaRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCREBelindaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREPuckRotation: public CachedRotationBase
{
PUBLISHED:
 WGCCREPuckRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREMirandaRotation: public CachedRotationBase
{
PUBLISHED:
 WGCCREMirandaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREArielRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCREArielRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREUmbrielRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCREUmbrielRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCRETitaniaRotation: public CachedRotationBase
{
PUBLISHED:
WGCCRETitaniaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREOberonRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCREOberonRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

// ############################################################################
// Neptune moons
// ############################################################################

class WGCCRENaiadRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCRENaiadRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREThalassaRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCREThalassaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREDespinaRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCREDespinaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREGalateaRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCREGalateaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCRELarissaRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCRELarissaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREProteusRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCREProteusRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCRETritonRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCRETritonRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

#endif //VSOP87_H
