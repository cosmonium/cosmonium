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
      double d0_rate, double meridian_angle, double mean_motion, double epoch,
      double validity = 10000.0);

  virtual LQuaterniond get_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond get_frame_rotation_at(double time);
  virtual bool is_flipped(void) const;

public:
  inline double get_T(double jd) const;

private:
  double a0;
  double a0_rate;
  double d0;
  double d0_rate;
  double meridian_angle;
  double mean_motion;
  bool flipped;
  double epoch;
  double validity;
};

class WGCCREComplexRotation: public CachedRotationBase
{
PUBLISHED:
  WGCCREComplexRotation(double epoch = 2451545.0, double validity = 10000.0);

public:
  inline double get_T(double jd) const;

protected:
  double epoch;
  double validity;
};

// ############################################################################
// Planets
// ############################################################################

class WGCCREMercuryRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREMercuryRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREMarsRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREMarsRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREJupiterRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREJupiterRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCRENeptuneRotation: public WGCCREComplexRotation
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

class WGCCRE9MoonRotation: public WGCCREComplexRotation
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

class WGCCREPhobosRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREPhobosRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREDeimosRotation: public WGCCREComplexRotation
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

class WGCCREAmaltheaRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREAmaltheaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREThebeRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREThebeRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREIoRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREIoRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREEuropaRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREEuropaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREGanymedeRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREGanymedeRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCRECallistoRotation: public WGCCREComplexRotation
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

class WGCCREEpimetheusRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREEpimetheusRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREJanusRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREJanusRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREMimasRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREMimasRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCRETethysRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCRETethysRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCRERheaRotation: public WGCCREComplexRotation
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

class WGCCRECordeliaRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCRECordeliaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREOpheliaRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREOpheliaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREBiancaRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREBiancaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCRECressidaRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCRECressidaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREDesdemonaRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREDesdemonaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREJulietRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREJulietRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREPortiaRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREPortiaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCRERosalindRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCRERosalindRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREBelindaRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREBelindaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREPuckRotation: public WGCCREComplexRotation
{
PUBLISHED:
 WGCCREPuckRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREMirandaRotation: public WGCCREComplexRotation
{
PUBLISHED:
 WGCCREMirandaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREArielRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREArielRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREUmbrielRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREUmbrielRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCRETitaniaRotation: public WGCCREComplexRotation
{
PUBLISHED:
WGCCRETitaniaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREOberonRotation: public WGCCREComplexRotation
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

class WGCCRENaiadRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCRENaiadRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREThalassaRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREThalassaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREDespinaRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREDespinaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREGalateaRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREGalateaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCRELarissaRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCRELarissaRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCREProteusRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREProteusRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

class WGCCRETritonRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCRETritonRotation() {}

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);
};

#endif //VSOP87_H
