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

#include "lunar_ephemeris.h"
#include "frames.h"
#include "dourneau.h"
#include "elp82.h"
#include "gust86.h"
#include "htc20.h"
#include "lieske_e5.h"
#include "pluto.h"
#include "rckin.h"
#include "vsop87.h"
#include "astro.h"

TypeHandle DourneauOrbit::_type_handle;

DourneauOrbit::DourneauOrbit(unsigned int planet_id,
    double average_period,
    double average_semi_major_axis,
    double average_eccentricity) :
    FunctionOrbit(new J2000EclipticReferenceFrame(), average_period * Day, average_semi_major_axis * Km, average_eccentricity),
    planet_id(planet_id)
{
}

DourneauOrbit::DourneauOrbit(DourneauOrbit const &other) :
        FunctionOrbit(other),
        planet_id(other.planet_id)
{
}

PT(OrbitBase)
DourneauOrbit::make_copy(void) const
{
  return new DourneauOrbit(*this);
}

LPoint3d
DourneauOrbit::get_frame_position_at(double time)
{
  return dourneau_sat_pos(time, planet_id);
}

LQuaterniond
DourneauOrbit::get_frame_rotation_at(double time)
{
  return LQuaterniond::ident_quat();
}

TypeHandle ELP82Orbit::_type_handle;

ELP82Orbit::ELP82Orbit(double average_period,
    double average_semi_major_axis,
    double average_eccentricity) :
    //TODO: The position is in the ecliptic plane of date, not J2000.0
    //The precession must be taken into account
    FunctionOrbit(new J2000EclipticReferenceFrame(), average_period * Day, average_semi_major_axis * Km, average_eccentricity)
{
}

ELP82Orbit::ELP82Orbit(ELP82Orbit const &other) :
        FunctionOrbit(other)
{
}

PT(OrbitBase)
ELP82Orbit::make_copy(void) const
{
  return new ELP82Orbit(*this);
}

LPoint3d
ELP82Orbit::get_frame_position_at(double time)
{
  return elp82_truncated_pos(time);
}

LQuaterniond
ELP82Orbit::get_frame_rotation_at(double time)
{
  return LQuaterniond::ident_quat();
}

TypeHandle Gust86Orbit::_type_handle;

Gust86Orbit::Gust86Orbit(unsigned int planet_id,
    double average_period,
    double average_semi_major_axis,
    double average_eccentricity) :
    FunctionOrbit(new J2000EclipticReferenceFrame(), average_period * Day, average_semi_major_axis * Km, average_eccentricity),
    planet_id(planet_id)
{
}

Gust86Orbit::Gust86Orbit(Gust86Orbit const &other) :
        FunctionOrbit(other),
        planet_id(other.planet_id)
{
}

PT(OrbitBase)
Gust86Orbit::make_copy(void) const
{
  return new Gust86Orbit(*this);
}

LPoint3d
Gust86Orbit::get_frame_position_at(double time)
{
  return gust86_sat_pos(time, planet_id);
}

LQuaterniond
Gust86Orbit::get_frame_rotation_at(double time)
{
  return LQuaterniond::ident_quat();
}

TypeHandle HTC20Orbit::_type_handle;

HTC20Orbit::HTC20Orbit(unsigned int planet_id,
    double average_period,
    double average_semi_major_axis,
    double average_eccentricity) :
    FunctionOrbit(new J2000EclipticReferenceFrame(), average_period * Day, average_semi_major_axis * Km, average_eccentricity),
    planet_id(planet_id)
{
}

HTC20Orbit::HTC20Orbit(HTC20Orbit const &other) :
        FunctionOrbit(other),
        planet_id(other.planet_id)
{
}

PT(OrbitBase)
HTC20Orbit::make_copy(void) const
{
  return new HTC20Orbit(*this);
}

LPoint3d
HTC20Orbit::get_frame_position_at(double time)
{
  return htc20_sat_pos(time, planet_id);
}

LQuaterniond
HTC20Orbit::get_frame_rotation_at(double time)
{
  return LQuaterniond::ident_quat();
}

TypeHandle LieskeE5Orbit::_type_handle;

LieskeE5Orbit::LieskeE5Orbit(unsigned int planet_id,
    double average_period,
    double average_semi_major_axis,
    double average_eccentricity) :
    FunctionOrbit(new J2000EclipticReferenceFrame(), average_period * Day, average_semi_major_axis * Km, average_eccentricity),
    planet_id(planet_id)
{
}

LieskeE5Orbit::LieskeE5Orbit(LieskeE5Orbit const &other) :
        FunctionOrbit(other),
        planet_id(other.planet_id)
{
}

PT(OrbitBase)
LieskeE5Orbit::make_copy(void) const
{
  return new LieskeE5Orbit(*this);
}

LPoint3d
LieskeE5Orbit::get_frame_position_at(double time)
{
  return lieske_e5_sat_pos(time, planet_id);
}

LQuaterniond
LieskeE5Orbit::get_frame_rotation_at(double time)
{
  return LQuaterniond::ident_quat();
}

TypeHandle MeeusPlutoOrbit::_type_handle;

MeeusPlutoOrbit::MeeusPlutoOrbit(double average_period,
    double average_semi_major_axis,
    double average_eccentricity) :
    FunctionOrbit(new J2000EclipticReferenceFrame(), average_period * JYear, average_semi_major_axis * AU, average_eccentricity)
{
}

MeeusPlutoOrbit::MeeusPlutoOrbit(MeeusPlutoOrbit const &other) :
        FunctionOrbit(other)
{
}

PT(OrbitBase)
MeeusPlutoOrbit::make_copy(void) const
{
  return new MeeusPlutoOrbit(*this);
}

LPoint3d
MeeusPlutoOrbit::get_frame_position_at(double time)
{
  return pluto_pos(time);
}

LQuaterniond
MeeusPlutoOrbit::get_frame_rotation_at(double time)
{
  return LQuaterniond::ident_quat();
}

TypeHandle RckinOrbit::_type_handle;

RckinOrbit::RckinOrbit(unsigned int planet_id,
    double average_period,
    double average_semi_major_axis,
    double average_eccentricity) :
    FunctionOrbit(new J2000EclipticReferenceFrame(), average_period * Day, average_semi_major_axis * Km, average_eccentricity),
    planet_id(planet_id)
{
}

RckinOrbit::RckinOrbit(RckinOrbit const &other) :
        FunctionOrbit(other),
        planet_id(other.planet_id)
{
}

PT(OrbitBase)
RckinOrbit::make_copy(void) const
{
  return new RckinOrbit(*this);
}

LPoint3d
RckinOrbit::get_frame_position_at(double time)
{
  return rckin_sat_pos(time, planet_id);
}

LQuaterniond
RckinOrbit::get_frame_rotation_at(double time)
{
  return LQuaterniond::ident_quat();
}

TypeHandle VSOP87Orbit::_type_handle;

VSOP87Orbit::VSOP87Orbit(unsigned int planet_id,
    double average_period,
    double average_semi_major_axis,
    double average_eccentricity) :
    FunctionOrbit(new J2000EclipticReferenceFrame(), average_period * JYear, average_semi_major_axis * AU, average_eccentricity),
    planet_id(planet_id)
{
}

VSOP87Orbit::VSOP87Orbit(VSOP87Orbit const &other) :
        FunctionOrbit(other),
        planet_id(other.planet_id)
{
}

PT(OrbitBase)
VSOP87Orbit::make_copy(void) const
{
  return new VSOP87Orbit(*this);
}

LPoint3d
VSOP87Orbit::get_frame_position_at(double time)
{
  return vsop87_pos(time, planet_id);
}

LQuaterniond
VSOP87Orbit::get_frame_rotation_at(double time)
{
  return LQuaterniond::ident_quat();
}
