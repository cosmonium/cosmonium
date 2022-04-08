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


#include "dynamicSceneManager.h"
#include "cameraHolder.h"
#include "collisionHandlerQueue.h"
#include "collisionNode.h"
#include "collisionRay.h"
#include "collisionTraverser.h"
#include "displayRegion.h"
#include "geomNode.h"
#include "graphicsOutput.h"
#include "perspectiveLens.h"
#include "dcast.h"


TypeHandle DynamicSceneManager::_type_handle;

bool DynamicSceneManager::auto_scale = true;
double DynamicSceneManager::min_scale = 0.02;
double DynamicSceneManager::max_scale = 1000.0;
bool DynamicSceneManager::set_frustum = true;
double DynamicSceneManager::mid_plane_ratio = 1.1;


DynamicSceneManager::DynamicSceneManager(NodePath render) :
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


DynamicSceneManager::~DynamicSceneManager(void)
{
}


void
DynamicSceneManager::set_target(GraphicsOutput *target)
{
  dr = target->make_display_region(0, 1, 0, 1);
  dr->disable_clears();
  dr->set_scissor_enabled(false);
  dr->set_camera(camera);
  dr->set_active(true);
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
  if (inverse_z) {
      lens->set_near_far(far_plane, near_plane);
  } else {
      lens->set_near_far(near_plane, far_plane);
  }
}


void
DynamicSceneManager::init_camera(CameraHolder *camera_holder, NodePath default_camera)
{
  camera = default_camera;
  lens = DCAST(PerspectiveLens, camera_holder->get_lens()->make_copy());
  DCAST(Camera, camera.node())->set_lens(lens);
  std::cout << "Planes: " << near_plane << " "  << far_plane << "\n";
  camera.reparent_to(root);
}


void
DynamicSceneManager::set_camera_mask(DrawMask flags)
{
  DCAST(Camera, camera.node())->set_camera_mask(flags);
}


void
DynamicSceneManager::update_scene_and_camera(double distance_to_nearest, CameraHolder *camera_holder)
{
  lens = DCAST(PerspectiveLens, camera_holder->get_lens()->make_copy());
  DCAST(Camera, camera.node())->set_lens(lens);
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
              near_plane = default_near_plane;
          }
      }
  }
  update_planes();
  if (auto_infinite_plane) {
      infinity = near_plane / lens_far_limit / 1000;
  } else {
      infinity = infinite_plane;
  }
  camera.set_pos(camera_holder->get_camera().get_pos());
  camera.set_quat(camera_holder->get_camera().get_quat());
}


void
DynamicSceneManager::build_scene(NodePath state, CameraHolder *camera_holder, SceneAnchorCollection visibles, SceneAnchorCollection resolved)
{
  root.set_state(state.get_state());
  //root.set_shader_input("midPlane", mid_plane);
}


PT(CollisionHandlerQueue)
DynamicSceneManager::pick_scene(LPoint2 mpos)
{
  CollisionTraverser picker;
  CollisionHandlerQueue *pq = new CollisionHandlerQueue();
  PT(CollisionNode) picker_node = new CollisionNode("mouseRay");
  NodePath picker_np = camera.attach_new_node(picker_node);
  picker_node->set_from_collide_mask(CollisionNode::get_default_collide_mask() | GeomNode::get_default_collide_mask());
  PT(CollisionRay) picker_ray = new CollisionRay();
  picker_ray->set_from_lens(DCAST(LensNode, camera.node()), mpos.get_x(), mpos.get_y());
  picker_node->add_solid(picker_ray);
  picker.add_collider(picker_np, pq);
  //picker.show_collisions(self.root);
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
  return camera;
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
