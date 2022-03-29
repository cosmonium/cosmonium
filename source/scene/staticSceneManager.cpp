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


#include "staticSceneManager.h"
#include "cameraHolder.h"
#include "displayRegion.h"
#include "graphicsOutput.h"
#include "perspectiveLens.h"
#include "dcast.h"


TypeHandle StaticSceneManager::_type_handle;

StaticSceneManager::StaticSceneManager(NodePath render) :
      near_plane(default_near_plane),
      infinity(0)
{
  if (infinite_far_plane && !inverse_z) {
      far_plane = std::numeric_limits<double>::infinity();
  } else {
      far_plane = default_far_plane;
  }
  root = render.attach_new_node("root");
}

StaticSceneManager::~StaticSceneManager(void)
{
}

void
StaticSceneManager::set_target(GraphicsOutput *target)
{
  dr = target->make_display_region(0, 1, 0, 1);
  dr->disable_clears();
  dr->set_scissor_enabled(false);
  dr->set_camera(camera);
  dr->set_active(true);
}

void
StaticSceneManager::attach_new_anchor(NodePath instance)
{
  instance.reparent_to(root);
}

void
StaticSceneManager::add_spread_object(NodePath instance)
{
  //Not supported by static scene manager
}

void
StaticSceneManager::add_background_object(NodePath instance)
{
  instance.reparent_to(root);
}

void
StaticSceneManager::init_camera(CameraHolder *camera_holder, NodePath default_camera)
{
  camera = default_camera;
  lens = DCAST(PerspectiveLens, camera_holder->get_lens()->make_copy());
  DCAST(Camera, camera.node())->set_lens(lens);
  if (auto_infinite_plane) {
      infinity = near_plane / lens_far_limit / 1000;
  } else {
      infinity = infinite_plane;
  }
  std::cout << "Planes: " << near_plane << " "  << far_plane << "\n";
  camera.reparent_to(root);
}

void
StaticSceneManager::set_camera_mask(DrawMask flags)
{
  DCAST(Camera, camera.node())->set_camera_mask(flags);
}

void
StaticSceneManager::update_scene_and_camera(double distance_to_nearest, CameraHolder *camera_holder)
{
  lens = DCAST(PerspectiveLens, camera_holder->get_lens()->make_copy());
  DCAST(Camera, camera.node())->set_lens(lens);
  if (inverse_z) {
      lens->set_near_far(far_plane, near_plane);
  } else {
      lens->set_near_far(near_plane, far_plane);
  }
  camera.set_pos(camera_holder->get_camera().get_pos());
  camera.set_quat(camera_holder->get_camera().get_quat());
}

void
StaticSceneManager::build_scene(NodePath state, CameraHolder *camera_holder, SceneAnchorCollection visibles, SceneAnchorCollection resolved)
{
  root.set_state(state.get_state());
}

void
StaticSceneManager::ls(void)
{
  root.ls();
}

NodePath
StaticSceneManager::get_camera(void)
{
  return camera;
}

NodePath
StaticSceneManager::get_root(void)
{
  return root;
}
