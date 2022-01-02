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


#include "cameraAnchor.h"
#include "infiniteFrustum.h"


TypeHandle CameraAnchor::_type_handle;

CameraAnchor::CameraAnchor(PyObject *ref_object, ReferenceFrame *frame) :
  CartesianAnchor(0, ref_object, frame),
  camera_vector(0.0)
{
}

CameraAnchor::~CameraAnchor(void)
{
}

void
CameraAnchor::do_update(void)
{
  CartesianAnchor::do_update();
  camera_vector = get_absolute_orientation().xform(LVector3d::forward());
}

InfiniteFrustum *
CameraAnchor::get_frustum(void)
{
  return frustum;
}

void
CameraAnchor::set_frustum(InfiniteFrustum *frustum)
{
  this->frustum = frustum;
}

InfiniteFrustum *
CameraAnchor::get_relative_frustum(void)
{
  return rel_frustum;
}

void
CameraAnchor::set_relative_frustum(InfiniteFrustum *frustum)
{
  this->rel_frustum = frustum;
}
