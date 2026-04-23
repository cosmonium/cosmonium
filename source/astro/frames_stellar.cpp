/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2024 Laurent Deru.
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

#include "frames_stellar.h"
#include "stellarAnchor.h"
#include "orbits.h"

TypeHandle StellarAnchorReferenceFrame::_type_handle;

StellarAnchorReferenceFrame::StellarAnchorReferenceFrame(StellarAnchor *anchor) :
    anchor(anchor)
{
}

StellarAnchorReferenceFrame::StellarAnchorReferenceFrame(StellarAnchorReferenceFrame const &other) :
    anchor(other.anchor)
{
}

PT(ReferenceFrame)
StellarAnchorReferenceFrame::make_copy(void) const
{
  return new StellarAnchorReferenceFrame(*this);
}

StellarAnchor *
StellarAnchorReferenceFrame::get_anchor(void)
{
  return anchor;
}

void
StellarAnchorReferenceFrame::set_anchor(StellarAnchor *anchor)
{
  this->anchor = anchor;
}

LPoint3d
StellarAnchorReferenceFrame::get_center(void)
{
  return anchor->get_local_position();
}

LPoint3d
StellarAnchorReferenceFrame::get_absolute_reference_point(void)
{
  return anchor->get_absolute_reference_point();
}

LQuaterniond
StellarAnchorReferenceFrame::get_orientation(void)
{
  return LQuaterniond::ident_quat();
}

TypeHandle OrbitReferenceFrame::_type_handle;

OrbitReferenceFrame::OrbitReferenceFrame(StellarAnchor *anchor) :
        StellarAnchorReferenceFrame(anchor)
{
}

OrbitReferenceFrame::OrbitReferenceFrame(OrbitReferenceFrame const &other) :
        StellarAnchorReferenceFrame(other.anchor)
{
}

PT(ReferenceFrame)
OrbitReferenceFrame::make_copy(void) const
{
  return new OrbitReferenceFrame(*this);
}

LQuaterniond
OrbitReferenceFrame::get_orientation(void)
{
  return anchor->get_orbit()->get_frame()->get_orientation();
}

TypeHandle EquatorialReferenceFrame::_type_handle;

EquatorialReferenceFrame::EquatorialReferenceFrame(StellarAnchor *anchor) :
        StellarAnchorReferenceFrame(anchor)
{
}

EquatorialReferenceFrame::EquatorialReferenceFrame(EquatorialReferenceFrame const &other) :
        StellarAnchorReferenceFrame(other.anchor)
{
}

PT(ReferenceFrame)
EquatorialReferenceFrame::make_copy(void) const
{
  return new EquatorialReferenceFrame(*this);
}

LQuaterniond
EquatorialReferenceFrame::get_orientation(void)
{
  return anchor->get_equatorial_rotation();
}

TypeHandle SynchroneReferenceFrame::_type_handle;

SynchroneReferenceFrame::SynchroneReferenceFrame(StellarAnchor *anchor) :
        StellarAnchorReferenceFrame(anchor)
{
}

SynchroneReferenceFrame::SynchroneReferenceFrame(SynchroneReferenceFrame const &other) :
        StellarAnchorReferenceFrame(other.anchor)
{
}

PT(ReferenceFrame)
SynchroneReferenceFrame::make_copy(void) const
{
  return new SynchroneReferenceFrame(*this);
}

LQuaterniond
SynchroneReferenceFrame::get_orientation(void)
{
  return anchor->get_sync_rotation();
}
