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

#include "patchBoundingBox.h"
#include "boundingBox.h"


PatchBoundingBox::PatchBoundingBox(const PTA_LVecBase3d &points) :
    points(points)
{
}

PatchBoundingBox::~PatchBoundingBox(void)
{
}


BoundingBox *
PatchBoundingBox::create_bounding_volume(LQuaterniond rot, LVector3d offset)
{
    PTA_LVecBase3d::const_iterator it;
    LPoint3d min_point(std::numeric_limits<double>::infinity());
    LPoint3d max_point(-std::numeric_limits<double>::infinity());

    for (it = points.begin(); it != points.end(); ++it) {
        LPoint3d point = rot.xform(*it + offset);
        for (unsigned int i = 0; i <3; ++i) {
            min_point[i] = std::min(min_point[i], point[i]);
            max_point[i] = std::max(max_point[i], point[i]);
        }
    }
    return new BoundingBox(LCAST(PN_stdfloat, min_point), LCAST(PN_stdfloat, max_point));
}


void
PatchBoundingBox::set_points(const PTA_LVecBase3d &points)
{
    this->points = points;
}


void
PatchBoundingBox::xform(LMatrix3d mat)
{
    PTA_LVecBase3d::iterator it;
    for (it = points.begin(); it != points.end(); ++it) {
        *it = mat.xform(*it);
    }
}
