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
#include "dcast.h"
#include "displayRegion.h"
#include "graphicsOutput.h"
#include "sceneAnchor.h"
#include "sceneManager.h"


TypeHandle SceneRegion::_type_handle;


SceneRegion::SceneRegion(SceneManager *scene_manager, double near, double far) :
    scene_manager(scene_manager),
    near(near),
    far(far),
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
    points.push_back(point);
    point->get_instance()->reparent_to(root);
}


bool
SceneRegion::overlap(SceneRegion *other)
{
    return ((near <= other->near) && (other->near < far)) || ((other->near <= near) && (near < other->far)) ||
           ((far >= other->far) && (other->far > near)) || ((other->far >= far) && (far > other->near));
}


void
SceneRegion::merge(SceneRegion *other)
{
    // TODO: See if move iterator should be used here
    bodies.insert(bodies.end(), other->bodies.begin(), other->bodies.end());
    near = std::min(near, other->near);
    far = std::max(far, other->far);
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
        lens->set_near_far(far * 1.01, near * 0.99);
    } else {
        lens->set_near_far(near * 0.99, far * 1.01);
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


void
SceneRegion::ls(void)
{
    std::cout << "Near " << near << " Far " << far << "\n";
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

std::vector<PT(SceneAnchor)> const &
SceneRegion::get_points(void) const
{
  return points;
}


double
SceneRegion::get_near(void) const
{
  return near;
}


double
SceneRegion::get_far(void) const
{
  return far;
}


NodePath
SceneRegion::get_root(void) const
{
  return root;
}
