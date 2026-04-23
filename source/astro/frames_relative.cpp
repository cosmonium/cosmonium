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

#include "frames_relative.h"

TypeHandle RelativeReferenceFrame::_type_handle;

RelativeReferenceFrame::RelativeReferenceFrame(ReferenceFrame *parent_frame, LPoint3d position, LQuaterniond orientation) :
    parent_frame(parent_frame),
    frame_position(position),
    frame_orientation(orientation)
{
}

RelativeReferenceFrame::RelativeReferenceFrame(RelativeReferenceFrame const &other) :
    parent_frame(other.parent_frame),
    frame_position(other.frame_position),
    frame_orientation(other.frame_orientation)
{
}

PT(ReferenceFrame)
RelativeReferenceFrame::make_copy(void) const
{
  return new RelativeReferenceFrame(*this);
}

LPoint3d
RelativeReferenceFrame::get_center(void)
{
  return parent_frame->get_local_position(frame_position);
}

LQuaterniond
RelativeReferenceFrame::get_orientation(void)
{
  return parent_frame->get_absolute_orientation(frame_orientation);
}

LPoint3d
RelativeReferenceFrame::get_absolute_reference_point(void)
{
  return parent_frame->get_absolute_reference_point();
}
