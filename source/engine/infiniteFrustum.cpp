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

#include "infiniteFrustum.h"
#include "boundingHexahedron.h"

TypeHandle InfiniteFrustum::_type_handle;

InfiniteFrustum::InfiniteFrustum(BoundingHexahedron const & frustum, const LMatrix4 &view_mat,
    const LPoint3d &view_position, bool zero_near):
  position(view_position)
{
  // Panda3D frustem has side planes stored from 0 to 3, near plane is 4 and far plane is 5
  // To make an infinite frustum, we drop the far plane
  for (int i = 0; i < 5; ++i) {
    LPlane plane = frustum.get_plane(i + 1) * view_mat;
    if (zero_near && i == 4) {
      // Set the distance of the near plane to 0
      plane[3] = 0.0;
    }
    planes[i][0] = plane[0];
    planes[i][1] = plane[1];
    planes[i][2] = plane[2];
    planes[i][3] = plane[3] - planes[i].get_normal().dot(position);
  }
}

InfiniteFrustum::~InfiniteFrustum(void)
{
}

LPoint3d
InfiniteFrustum::get_position(void) const
{
  return position;
}

bool
InfiniteFrustum::is_sphere_in(LPoint3d const &center, double radius) const
{
  for (auto plane : planes) {
    double dist = plane.dist_to_plane(center);
    if (dist > radius) {
      return false;
    }
  }
  return true;
}
