/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2023 Laurent Deru.
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


#include "dynamicSceneManager.h"
#include "bitMask.h"
#include "cameraHolder.h"
#include "collisionHandlerQueue.h"
#include "collisionNode.h"
#include "collisionRay.h"
#include "collisionTraverser.h"
#include "directionalLight.h"
#include "displayRegion.h"
#include "geomNode.h"
#include "graphicsOutput.h"
#include "perspectiveLens.h"
#include "renderPass.h"
#include "settings.h"
#include "dcast.h"


TypeHandle DynamicSceneManager::_type_handle;


bool DynamicSceneManager::auto_scale = true;
double DynamicSceneManager::min_scale = 0.02;
double DynamicSceneManager::max_scale = 1000.0;
bool DynamicSceneManager::set_frustum = true;
double DynamicSceneManager::mid_plane_ratio = 1.1;


DynamicSceneManager::DynamicSceneManager(NodePath render) :
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
  PT(DirectionalLight) directional_light = new DirectionalLight("fake-light");
  directional_light->set_color(LColor(0));
  fake_light = root.attach_new_node(directional_light);
}


DynamicSceneManager::~DynamicSceneManager(void)
{
}


bool DynamicSceneManager::has_regions(void) const
{
  return false;
}


void
DynamicSceneManager::add_pass(const std::string &name, GraphicsOutput *target, DrawMask camera_mask)
{
  PT(RenderPass) rendering_pass = new RenderPass(name, target, camera_mask);
  DCAST(Camera, rendering_pass->camera.node())->set_lens(lens);
  rendering_pass->camera.reparent_to(root);
  rendering_pass->create();
  rendering_passes.push_back(rendering_pass);
}


void
DynamicSceneManager::attach_new_anchor(NodePath instance)
{
  instance.reparent_to(root);
}


void
DynamicSceneManager::add_spread_object(NodePath instance)
{
  //Not supported by static scene manager
}


void
DynamicSceneManager::add_background_object(NodePath instance)
{
  instance.reparent_to(root);
}


void
DynamicSceneManager::update_planes(void)
{
  Settings *settings = Settings::get_global_ptr();
  if (settings->inverse_z) {
      lens->set_near_far(far_plane, near_plane);
  } else {
      lens->set_near_far(near_plane, far_plane);
  }
}


void
DynamicSceneManager::init_camera(CameraHolder *camera_holder, NodePath default_camera)
{
  lens = DCAST(PerspectiveLens, camera_holder->get_lens()->make_copy());
  std::cout << "Planes: " << near_plane << " "  << far_plane << "\n";
}


void
DynamicSceneManager::update_scene_and_camera(double distance_to_nearest, CameraHolder *camera_holder)
{
  Settings *settings = Settings::get_global_ptr();
  lens = DCAST(PerspectiveLens, camera_holder->get_lens()->make_copy());
  if (auto_scale) {
      if (false) {//distance_to_nearest)
          scale = max_scale;
      } else if (distance_to_nearest <= 0) {
          scale = min_scale;
      } else if (distance_to_nearest < max_scale * 10) {
          scale = std::max(distance_to_nearest / 10, min_scale);
      } else {
          scale = max_scale;
      }
      if (set_frustum) {
          //near_plane = min(distance_to_nearest / settings.scale / 2.0, settings.near_plane)
          if (scale < 1.0) {
              near_plane = scale;
          } else {
              near_plane = settings->default_near_plane;
          }
      }
  }
  update_planes();
  if (settings->auto_infinite_plane) {
      infinity = near_plane / settings->lens_far_limit / 1000;
  } else {
      infinity = settings->infinite_plane;
  }
  mid_plane = infinity / mid_plane_ratio;
  for (auto rendering_pass : rendering_passes) {
    DCAST(Camera, rendering_pass->camera.node())->set_lens(lens);
    rendering_pass->camera.set_pos(camera_holder->get_camera().get_pos());
    rendering_pass->camera.set_quat(camera_holder->get_camera().get_quat());
  }
}


void
DynamicSceneManager::build_scene(NodePath state, CameraHolder *camera_holder, SceneAnchorCollection visibles, SceneAnchorCollection resolved)
{
  root.set_state(state.get_state());
  CPT(InternalName) name = InternalName::make("midPlane");
  root.set_shader_input(name, LVecBase4(mid_plane));
  root.set_light(fake_light);
}


PT(CollisionHandlerQueue)
DynamicSceneManager::pick_scene(LPoint2 mpos)
{
  Settings *settings = Settings::get_global_ptr();
  CollisionTraverser picker;
  CollisionHandlerQueue *pq = new CollisionHandlerQueue();
  PT(CollisionNode) picker_node = new CollisionNode("mouseRay");
  NodePath picker_np = rendering_passes[0]->camera.attach_new_node(picker_node);
  picker_node->set_from_collide_mask(BitMask32::bit(settings->mouse_click_collision_bit));
  PT(CollisionRay) picker_ray = new CollisionRay();
  picker_ray->set_from_lens(DCAST(LensNode, rendering_passes[0]->camera.node()), mpos.get_x(), mpos.get_y());
  picker_node->add_solid(picker_ray);
  picker.add_collider(picker_np, pq);
  //picker.show_collisions(root);
  picker.traverse(root);
  pq->sort_entries();
  picker_np.remove_node();
  return pq;
}


void
DynamicSceneManager::ls(void)
{
  root.ls();
}


NodePath
DynamicSceneManager::get_camera(void)
{
  return rendering_passes[0]->camera;
}


double
DynamicSceneManager::get_infinity(void) const
{
  return infinity;
}


NodePath
DynamicSceneManager::get_root(void)
{
  return root;
}
