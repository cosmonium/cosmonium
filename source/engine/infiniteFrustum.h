/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2019 Laurent Deru.
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

#ifndef INFINITE_FRUSTUM_H
#define INFINITE_FRUSTUM_H

#include "pandabase.h"
#include "luse.h"
#include "plane.h"
#include "referenceCount.h"
#include"type_utils.h"

class BoundingHexahedron;

class InfiniteFrustum : public TypedObject, public ReferenceCount
{
PUBLISHED:
    InfiniteFrustum(BoundingHexahedron const & frustum, const LMatrix4 &view_mat,
        const LPoint3d &view_position, bool zero_near=true);
    virtual ~InfiniteFrustum(void);
    bool is_sphere_in(LPoint3d const &center, double radius) const;

    LPoint3d get_position(void) const;

protected:
    LPlaned planes[5];
    LPoint3d position;
    MAKE_TYPE_2("InfiniteFrustum", TypedObject, ReferenceCount);
};

#endif //INFINITE_FRUSTUM_H

