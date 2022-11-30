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
#include "rotations.h"

class WGCCRESimpleRotation: public RotationBase
{
PUBLISHED:
  WGCCRESimpleRotation(double a0, double d0, double meridian_angle,
      double mean_motion, double epoch);

protected:
  WGCCRESimpleRotation(WGCCRESimpleRotation const &other);

PUBLISHED:
  virtual PT(RotationBase) make_copy(void) const;

  virtual LQuaterniond get_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond get_frame_rotation_at(double time);
  virtual bool is_flipped(void) const;

private:
  LQuaterniond orientation;
  double meridian_angle;
  double mean_motion;
  bool flipped;
  double epoch;

  MAKE_TYPE("WGCCRESimpleRotation", RotationBase);
};

class WGCCRESimplePrecessingRotation: public RotationBase
{
PUBLISHED:
  WGCCRESimplePrecessingRotation(double a0, double a0_rate, double d0,
      double d0_rate, double meridian_angle, double mean_motion, double epoch,
      double validity = 10000.0);

protected:
  WGCCRESimplePrecessingRotation(WGCCRESimplePrecessingRotation const &other);

PUBLISHED:
  virtual PT(RotationBase) make_copy(void) const;

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

  MAKE_TYPE("WGCCRESimplePrecessingRotation", RotationBase);
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

  MAKE_TYPE("WGCCREComplexRotation", RotationBase);
};

// ############################################################################
// Planets
// ############################################################################

class WGCCREMercuryRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREMercuryRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREMercuryRotation", WGCCREComplexRotation);
};

class WGCCREMarsRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREMarsRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREMarsRotation", WGCCREComplexRotation);
};

class WGCCREJupiterRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREJupiterRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREJupiterRotation", WGCCREComplexRotation);
};

class WGCCRENeptuneRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCRENeptuneRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCRENeptuneRotation", WGCCREComplexRotation);
};

// ############################################################################
// Moon
// ############################################################################

class WGCCRE9MoonRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCRE9MoonRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCRE9MoonRotation", WGCCREComplexRotation);
};

// ############################################################################
// Mars moons
// ############################################################################

class WGCCREPhobosRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREPhobosRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREPhobosRotation", WGCCREComplexRotation);
};

class WGCCREDeimosRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREDeimosRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREDeimosRotation", WGCCREComplexRotation);
};

// ############################################################################
// Jupiter moons
// ############################################################################

class WGCCREAmaltheaRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREAmaltheaRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREAmaltheaRotation", WGCCREComplexRotation);
};

class WGCCREThebeRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREThebeRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREThebeRotation", WGCCREComplexRotation);
};

class WGCCREIoRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREIoRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREIoRotation", WGCCREComplexRotation);
};

class WGCCREEuropaRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREEuropaRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREEuropaRotation", WGCCREComplexRotation);
};

class WGCCREGanymedeRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREGanymedeRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREGanymedeRotation", WGCCREComplexRotation);
};

class WGCCRECallistoRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCRECallistoRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCRECallistoRotation", WGCCREComplexRotation);
};

// ############################################################################
// Saturn moons
// ############################################################################

class WGCCREEpimetheusRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREEpimetheusRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREEpimetheusRotation", WGCCREComplexRotation);
};

class WGCCREJanusRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREJanusRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREJanusRotation", WGCCREComplexRotation);
};

class WGCCREMimasRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREMimasRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREMimasRotation", WGCCREComplexRotation);
};

class WGCCRETethysRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCRETethysRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCRETethysRotation", WGCCREComplexRotation);
};

class WGCCRERheaRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCRERheaRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCRERheaRotation", WGCCREComplexRotation);
};

// ############################################################################
// Uranus moons
// ############################################################################

class WGCCRECordeliaRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCRECordeliaRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCRECordeliaRotation", WGCCREComplexRotation);
};

class WGCCREOpheliaRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREOpheliaRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREOpheliaRotation", WGCCREComplexRotation);
};

class WGCCREBiancaRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREBiancaRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREBiancaRotation", WGCCREComplexRotation);
};

class WGCCRECressidaRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCRECressidaRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCRECressidaRotation", WGCCREComplexRotation);
};

class WGCCREDesdemonaRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREDesdemonaRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREDesdemonaRotation", WGCCREComplexRotation);
};

class WGCCREJulietRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREJulietRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREJulietRotation", WGCCREComplexRotation);
};

class WGCCREPortiaRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREPortiaRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREPortiaRotation", WGCCREComplexRotation);
};

class WGCCRERosalindRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCRERosalindRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCRERosalindRotation", WGCCREComplexRotation);
};

class WGCCREBelindaRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREBelindaRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREBelindaRotation", WGCCREComplexRotation);
};

class WGCCREPuckRotation: public WGCCREComplexRotation
{
PUBLISHED:
 WGCCREPuckRotation() {}

 virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREPuckRotation", WGCCREComplexRotation);
};

class WGCCREMirandaRotation: public WGCCREComplexRotation
{
PUBLISHED:
 WGCCREMirandaRotation() {}

 virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREMirandaRotation", WGCCREComplexRotation);
};

class WGCCREArielRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREArielRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREArielRotation", WGCCREComplexRotation);
};

class WGCCREUmbrielRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREUmbrielRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREUmbrielRotation", WGCCREComplexRotation);
};

class WGCCRETitaniaRotation: public WGCCREComplexRotation
{
PUBLISHED:
WGCCRETitaniaRotation() {}

virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCRETitaniaRotation", WGCCREComplexRotation);
};

class WGCCREOberonRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREOberonRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREOberonRotation", WGCCREComplexRotation);
};

// ############################################################################
// Neptune moons
// ############################################################################

class WGCCRENaiadRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCRENaiadRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCRENaiadRotation", WGCCREComplexRotation);
};

class WGCCREThalassaRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREThalassaRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREThalassaRotation", WGCCREComplexRotation);
};

class WGCCREDespinaRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREDespinaRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREDespinaRotation", WGCCREComplexRotation);
};

class WGCCREGalateaRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREGalateaRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREGalateaRotation", WGCCREComplexRotation);
};

class WGCCRELarissaRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCRELarissaRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCRELarissaRotation", WGCCREComplexRotation);
};

class WGCCREProteusRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCREProteusRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCREProteusRotation", WGCCREComplexRotation);
};

class WGCCRETritonRotation: public WGCCREComplexRotation
{
PUBLISHED:
  WGCCRETritonRotation() {}

  virtual PT(RotationBase) make_copy(void) const;

public:
  virtual LQuaterniond calc_frame_equatorial_orientation_at(double time);
  virtual LQuaterniond calc_frame_rotation_at(double time);

  MAKE_TYPE("WGCCRETritonRotation", WGCCREComplexRotation);
};

#endif //VSOP87_H
