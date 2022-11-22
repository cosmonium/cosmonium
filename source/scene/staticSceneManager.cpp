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
#include "renderPass.h"
#include "settings.h"
#include "dcast.h"


TypeHandle StaticSceneManager::_type_handle;


StaticSceneManager::StaticSceneManager(NodePath render) :
      infinity(0)
{
  Settings *settings = Settings::get_global_ptr();
  near_plane = settings->default_near_plane;
  if (settings->infinite_far_plane && !settings->inverse_z) {
      far_plane = std::numeric_limits<double>::infinity();
  } else {
      far_plane = settings->default_far_plane;
  }
  root = render.attach_new_node("root");
}


StaticSceneManager::~StaticSceneManager(void)
{
}


bool StaticSceneManager::has_regions(void) const
{
  return false;
}


void
StaticSceneManager::add_pass(const std::string &name, GraphicsOutput *target, DrawMask camera_mask)
{
  PT(RenderPass) rendering_pass = new RenderPass(name, target, camera_mask);
  DCAST(Camera, rendering_pass->camera.node())->set_lens(lens);
  rendering_pass->camera.reparent_to(root);
  rendering_pass->create();
  rendering_passes.push_back(rendering_pass);
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
  Settings *settings = Settings::get_global_ptr();
  lens = DCAST(PerspectiveLens, camera_holder->get_lens()->make_copy());
  if (settings->auto_infinite_plane) {
      infinity = near_plane / settings->lens_far_limit / 1000;
  } else {
      infinity = settings->infinite_plane;
  }
  std::cout << "Planes: " << near_plane << " "  << far_plane << "\n";
}


void
StaticSceneManager::update_scene_and_camera(double distance_to_nearest, CameraHolder *camera_holder)
{
  Settings *settings = Settings::get_global_ptr();
  lens = DCAST(PerspectiveLens, camera_holder->get_lens()->make_copy());
  if (settings->inverse_z) {
      lens->set_near_far(far_plane, near_plane);
  } else {
      lens->set_near_far(near_plane, far_plane);
  }
  for (auto rendering_pass : rendering_passes) {
    DCAST(Camera, rendering_pass->camera.node())->set_lens(lens);
    rendering_pass->camera.set_pos(camera_holder->get_camera().get_pos());
    rendering_pass->camera.set_quat(camera_holder->get_camera().get_quat());
  }
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
  return rendering_passes[0]->camera;
}


double
StaticSceneManager::get_infinity(void) const
{
  return 0.0;
}


NodePath
StaticSceneManager::get_root(void)
{
  return root;
}
