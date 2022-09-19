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


#include "sceneRegion.h"
#include "camera.h"
#include "cameraHolder.h"
#include "collisionHandlerQueue.h"
#include "collisionNode.h"
#include "collisionRay.h"
#include "collisionTraverser.h"
#include "dcast.h"
#include "displayRegion.h"
#include "graphicsOutput.h"
#include "renderPass.h"
#include "sceneAnchor.h"
#include "sceneManager.h"


TypeHandle SceneRegion::_type_handle;


SceneRegion::SceneRegion(SceneManager *scene_manager, double near_distance, double far_distance) :
    scene_manager(scene_manager),
    near_distance(near_distance),
    far_distance(far_distance),
    root(NodePath("root"))
{
}


SceneRegion::~SceneRegion(void)
{
}


void
SceneRegion::add_body(SceneAnchor *body)
{
    bodies.push_back(body);
}


void
SceneRegion::add_point(SceneAnchor *point)
{
    points.add_scene_anchor(point);
    point->get_instance()->reparent_to(root);
}


bool
SceneRegion::overlap(SceneRegion *other)
{
    return ((near_distance <= other->near_distance) && (other->near_distance < far_distance)) || ((other->near_distance <= near_distance) && (near_distance < other->far_distance)) ||
           ((far_distance >= other->far_distance) && (other->far_distance > near_distance)) || ((other->far_distance >= far_distance) && (far_distance > other->near_distance));
}


bool
SceneRegion::overlap(double near_distance, double far_distance)
{
    return ((near_distance <= near_distance) && (near_distance < far_distance)) || ((near_distance <= near_distance) && (near_distance < far_distance)) ||
           ((far_distance >= far_distance) && (far_distance > near_distance)) || ((far_distance >= far_distance) && (far_distance > near_distance));
}


void
SceneRegion::merge(SceneRegion *other)
{
    // TODO: See if move iterator should be used here
    bodies.insert(bodies.end(), other->bodies.begin(), other->bodies.end());
    near_distance = std::min(near_distance, other->near_distance);
    far_distance = std::max(far_distance, other->far_distance);
}


void
SceneRegion::create(std::vector<PT(RenderPass)> parent_rendering_passes,
    const RenderState *state,
    CameraHolder *camera_holder,
    bool inverse_z,
    double section_near,
    double section_far,
    int sort_index)
{
    root.set_state(state);
    for (auto body : bodies) {
        NodePath * instance = body->get_instance();
        if (instance->has_parent()) {
          NodePath clone = root.attach_new_node("region-anchor");
          instance->instance_to(clone);
        } else {
          instance->reparent_to(root);
        }
    }
    PT(PerspectiveLens) lens = DCAST(PerspectiveLens, camera_holder->get_lens()->make_copy());
    if (inverse_z) {
        lens->set_near_far(far_distance, near_distance);
    } else {
        lens->set_near_far(near_distance, far_distance);
    }
    for (auto parent_rendering_pass : parent_rendering_passes) {
      PT(RenderPass) rendering_pass = new RenderPass(*parent_rendering_pass);
      rendering_pass->camera.reparent_to(root);
      rendering_pass->create();
      DCAST(Camera, rendering_pass->camera.node())->set_lens(lens);
      rendering_pass->camera.set_pos(camera_holder->get_camera().get_pos());
      rendering_pass->camera.set_quat(camera_holder->get_camera().get_quat());
      rendering_pass->display_region->set_sort(sort_index);
      if (inverse_z) {
        rendering_pass->display_region->set_depth_range(section_far, section_near);
      } else {
        rendering_pass->display_region->set_depth_range(section_near, section_far);
      }
      rendering_passes.push_back(rendering_pass);
    }
}


void
SceneRegion::remove(void)
{
  for (auto rendering_pass : rendering_passes) {
    rendering_pass->remove();
  }
  rendering_passes.clear();
}


PT(CollisionHandlerQueue)
SceneRegion::pick_scene(LPoint2 mpos)
{
  NodePath cam_np = rendering_passes[0]->camera;
  CollisionTraverser picker;
  CollisionHandlerQueue *pq = new CollisionHandlerQueue();
  PT(CollisionNode) picker_node = new CollisionNode("mouseRay");
  NodePath picker_np = cam_np.attach_new_node(picker_node);
  picker_node->set_from_collide_mask(CollisionNode::get_default_collide_mask() | GeomNode::get_default_collide_mask());
  PT(CollisionRay) picker_ray = new CollisionRay();
  picker_ray->set_from_lens(DCAST(LensNode, cam_np.node()), mpos.get_x(), mpos.get_y());
  picker_node->add_solid(picker_ray);
  picker.add_collider(picker_np, pq);
  //picker.show_collisions(self.root);
  picker.traverse(root);
  pq->sort_entries();
  picker_np.remove_node();
  return pq;
}


void
SceneRegion::ls(void)
{
    std::cout << "Near " << near_distance << " Far " << far_distance << "\n";
    //print("Bodies:", list(map(lambda b: b.get_name(), self.bodies)))
    root.ls();
}


int
SceneRegion::get_num_points() const
{
  return points.size();
}


SceneAnchor *
SceneRegion::get_point(int index) const
{
  return points[index];
}


SceneAnchorCollection
SceneRegion::get_points_collection(void)
{
  return points;
}


double
SceneRegion::get_near(void) const
{
  return near_distance;
}


double
SceneRegion::get_far(void) const
{
  return far_distance;
}


NodePath
SceneRegion::get_root(void) const
{
  return root;
}
