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
SceneRegion::set_camera_mask(DrawMask flags)
{
    cam->set_camera_mask(flags);
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


void
SceneRegion::merge(SceneRegion *other)
{
    // TODO: See if move iterator should be used here
    bodies.insert(bodies.end(), other->bodies.begin(), other->bodies.end());
    near_distance = std::min(near_distance, other->near_distance);
    far_distance = std::max(far_distance, other->far_distance);
}


void
SceneRegion::create(GraphicsOutput *target,
    const RenderState *state,
    CameraHolder *camera_holder,
    DrawMask camera_mask,
    bool inverse_z,
    double section_near,
    double section_far,
    int sort_index)
{
    this->target = target;
    root.set_state(state);
    for (auto body : bodies) {
        body->get_instance()->reparent_to(root);
    }
    cam = new Camera("region-cam");
    cam->set_camera_mask(camera_mask);
    PT(PerspectiveLens) lens = DCAST(PerspectiveLens, camera_holder->get_lens()->make_copy());
    if (inverse_z) {
        lens->set_near_far(far_distance * 1.01, near_distance * 0.99);
    } else {
        lens->set_near_far(near_distance * 0.99, far_distance * 1.01);
    }
    cam->set_lens(lens);
    cam_np = root.attach_new_node(cam);
    cam_np.set_quat(camera_holder->get_camera().get_quat());
    region = target->make_display_region(0, 1, 0, 1);
    region->disable_clears();
    // region.setClearColorActive(1)
    // region.setClearColor((1, 0, 0, 1))
    region->set_camera(cam_np);
    region->set_scissor_enabled(false);
    region->set_sort(sort_index);
    if (inverse_z) {
        region->set_depth_range(section_far, section_near);
    } else {
        region->set_depth_range(section_near, section_far);
    }
}


void
SceneRegion::remove(void)
{
    target->remove_display_region(region);
}


PT(CollisionHandlerQueue)
SceneRegion::pick_scene(LPoint2 mpos)
{
  CollisionTraverser picker;
  CollisionHandlerQueue *pq = new CollisionHandlerQueue();
  PT(CollisionNode) picker_node = new CollisionNode("mouseRay");
  NodePath picker_np = cam_np.attach_new_node(picker_node);
  picker_node->set_from_collide_mask(CollisionNode::get_default_collide_mask() | GeomNode::get_default_collide_mask());
  PT(CollisionRay) picker_ray = new CollisionRay();
  picker_ray->set_from_lens(DCAST(LensNode, cam), mpos.get_x(), mpos.get_y());
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
