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


#include "renderPass.h"

#include "displayRegion.h"
#include "graphicsOutput.h"
#include "perspectiveLens.h"


RenderPass::RenderPass(const std::string &name, GraphicsOutput *target, DrawMask camera_mask) :
  name(name),
  target(target),
  camera_mask(camera_mask)
{
  PT(Camera) node = new Camera("camera");
  node->set_camera_mask(camera_mask);
  camera = NodePath(node);
}


RenderPass::RenderPass(RenderPass& other) :
    name(other.name),
    target(other.target),
    camera_mask(other.camera_mask)
{
  PT(Camera) node = new Camera("camera");
  node->set_camera_mask(camera_mask);
  camera = NodePath(node);
}


RenderPass::~RenderPass(void)
{
  if (display_region != nullptr) {
    target->remove_display_region(display_region);
  }
}


void
RenderPass::create(void)
{
  display_region = target->make_display_region(0, 1, 0, 1);
  display_region->disable_clears();
  display_region->set_scissor_enabled(false);
  display_region->set_camera(camera);
  display_region->set_active(true);
}


void
RenderPass::remove(void)
{
  target->remove_display_region(display_region);
  display_region = nullptr;
}
