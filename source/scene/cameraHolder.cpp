/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2022 Laurent Deru.
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


#include "cameraHolder.h"
#include "cameraAnchor.h"
#include "perspectiveLens.h"


TypeHandle CameraHolder::_type_handle;


CameraHolder::CameraHolder(CameraAnchor *anchor, NodePath camera, PerspectiveLens *lens) :
    anchor(anchor),
    camera(camera),
    lens(lens)
{
}


CameraHolder::~CameraHolder(void)
{
}


CameraAnchor *
CameraHolder::get_anchor(void)
{
  return anchor;
}


void
CameraHolder::set_anchor(CameraAnchor *anchor)
{
  this->anchor = anchor;
}


NodePath
CameraHolder::get_camera(void)
{
  return camera;
}


void
CameraHolder::set_camera(NodePath camera)
{
  this->camera = camera;
}


double
CameraHolder::get_cos_fov2(void)
{
  return cos_fov2;
}


void
CameraHolder::set_cos_fov2(double cos_fov2)
{
  this->cos_fov2 = cos_fov2;
}


PerspectiveLens *
CameraHolder::get_lens(void)
{
  return lens;
}
