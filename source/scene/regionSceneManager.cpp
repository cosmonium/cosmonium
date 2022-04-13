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


#include "regionSceneManager.h"
#include "anchor.h"
#include "cameraAnchor.h"
#include "cameraHolder.h"
#include "collisionEntriesCollection.h"
#include "collisionHandlerQueue.h"
#include "displayRegion.h"
#include "graphicsOutput.h"
#include "perspectiveLens.h"
#include "sceneAnchor.h"
#include "sceneAnchorCollection.h"
#include "sceneRegion.h"
#include "dcast.h"


TypeHandle RegionSceneManager::_type_handle;

double RegionSceneManager::min_near = 1e-6;
double RegionSceneManager::max_near_reagion = 1e5;
double RegionSceneManager::infinity = 1e9;


static PStatCollector _build_scene_collector("Engine:build_scene");


RegionSceneManager::RegionSceneManager(void)
{
}


RegionSceneManager::~RegionSceneManager(void)
{
}


void
RegionSceneManager::set_target(GraphicsOutput *target)
{
  this->target = target;
}


void
RegionSceneManager::attach_new_anchor(NodePath instance)
{
}


void
RegionSceneManager::add_spread_object(NodePath instance)
{
  spread_objects.push_back(instance);
}


void
RegionSceneManager::attach_spread_objects(void)
{
    for (auto spread_object : spread_objects) {
        for (auto region : regions) {
            NodePath clone = region->get_root().attach_new_node("clone");
            clone.set_transform(spread_object.get_parent().get_net_transform());
            spread_object.instance_to(clone);
        }
    }
}


void
RegionSceneManager::add_background_object(NodePath instance)
{
  instance.reparent_to(background_region->get_root());
}


void
RegionSceneManager::init_camera(CameraHolder *camera_holder, NodePath default_camera)
{
}


void
RegionSceneManager::set_camera_mask(DrawMask flags)
{
  camera_mask = flags;
  for (auto region : regions) {
      region->set_camera_mask(flags);
  }
}


void
RegionSceneManager::update_scene_and_camera(double distance_to_nearest, CameraHolder *camera_holder)
{
}


void
RegionSceneManager::clear_scene(void)
{
    for (auto region : regions) {
        region->remove();
    }
    regions.clear();
}


void
RegionSceneManager::build_scene(NodePath world, CameraHolder *camera_holder, SceneAnchorCollection visibles, SceneAnchorCollection resolveds)
{
  _build_scene_collector.start();

  const RenderState *state = world.get_state();
  clear_scene();
  std::vector<PT(SceneAnchor)> background_resolved;
  for (unsigned int i = 0; i < resolveds.get_num_scene_anchors(); ++i) {
      SceneAnchor *resolved = resolveds[i];
      AnchorBase *anchor = resolved->get_anchor();
      if (!anchor->visible) {
        continue;
      }
      if (!resolved->get_virtual_object() && resolved->get_instance() != nullptr) {
          if (!resolved->get_background()) {
              double near;
              double far;
              if (anchor->distance_to_obs > anchor->get_bounding_radius()) {
                  double coef = -anchor->vector_to_obs.dot(camera_holder->get_anchor()->camera_vector);
                  near = (anchor->distance_to_obs  - anchor->get_bounding_radius()) * coef  * camera_holder->get_cos_fov2() / scale;
                  far = (anchor->distance_to_obs + anchor->get_bounding_radius()) * coef / scale;
                  near = std::max(near, min_near);
              } else {
                  near = min_near;
                  far = min_near + anchor->get_bounding_radius() * 2 / scale;
              }
              SceneRegion *region = new SceneRegion(this, near, far);
              region->add_body(resolved);
              while (regions.size() > 0 && region->overlap(regions.back())) {
                  region->merge(regions.back());
                  regions.pop_back();
              }
              regions.push_back(region);
          } else {
              background_resolved.push_back(resolved);
          }
      }
  }
  if (regions.size() > 0) {
      // Sort the region from nearest to farthest
      regions.sort([](const SceneRegion *a, SceneRegion *b ) { return a->get_near() < b->get_near(); });
      std::list<PT(SceneRegion)> embedded_regions;
      SceneRegion *prev_region = regions.front();
      for (auto next_region_it = ++regions.begin(); next_region_it != regions.end(); ++next_region_it) {
        SceneRegion *next_region = *next_region_it;
          if (prev_region->get_far() != next_region->get_near()) {
              SceneRegion *embedded_region = new SceneRegion(this, prev_region->get_far(), next_region->get_near());
              embedded_regions.push_back(embedded_region);
          }
          prev_region = next_region;
      }
      regions.merge(embedded_regions);
      regions.sort([](const SceneRegion *a, SceneRegion *b ) { return a->get_near() < b->get_near(); });
      SceneRegion *farthest_region = new SceneRegion(this, regions.back()->get_far(), std::numeric_limits<double>::infinity());
      regions.push_back(farthest_region);
      if (regions.front()->get_near() > min_near) {
          if (regions.front()->get_near() / min_near > max_near_reagion) {
              SceneRegion *nearest_region = new SceneRegion(this, min_near * max_near_reagion, regions.front()->get_near());
              regions.push_front(nearest_region);
              nearest_region = new SceneRegion(this, min_near, min_near * max_near_reagion);
              regions.push_front(nearest_region);
          } else {
              SceneRegion *nearest_region = new SceneRegion(this, min_near, regions.front()->get_near());
              regions.push_front(nearest_region);
          }
      }
      background_region = farthest_region;
  } else {
      SceneRegion *region = new SceneRegion(this, min_near, std::numeric_limits<double>::infinity());
      regions.push_back(region);
      background_region = region;
  }
  background_region = regions.back();
  for (auto body : background_resolved) {
      background_region->add_body(body);
  }
  auto current_region_it = regions.begin();
  SceneRegion * current_region= *current_region_it;
  for (unsigned int i = 0; i < visibles.get_num_scene_anchors(); ++i) {
      SceneAnchor *visible = visibles[i];
      AnchorBase *anchor = visible->get_anchor();
      if (anchor->resolved) {
          continue;
      }
      while (anchor->z_distance  / scale > current_region->get_far()) {
          ++current_region_it;
          current_region = *current_region_it;
      }
      current_region->add_point(visible);
  }
  if (regions.size() > 0) {
      double region_size = 1.0 / regions.size();
      double base;
      if (!inverse_z) {
          // Start with the nearest region, which will start a depth 0 (i.e. near plane)
          base = 0.0;
      } else {
          base = 1.0;
          region_size = -region_size;
      }
      unsigned int i = 0;
      for (auto region : regions) {
          int sort_index = regions.size() - i;
          region->create(target, state, camera_holder, camera_mask, inverse_z, base, std::min(base + region_size, 1 - 1e-6), sort_index);
          base += region_size;
          ++i;
      }
  }
  attach_spread_objects();
  spread_objects.clear();

  _build_scene_collector.stop();
}


PT(CollisionEntriesCollection)
RegionSceneManager::pick_scene(LPoint2 mpos)
{
  CollisionEntriesCollection *entries = new CollisionEntriesCollection();
  for (auto region : regions) {
    PT(CollisionHandlerQueue) pq = region->pick_scene(mpos);
    entries->add_entries(pq);
  }
  return entries;
}


void
RegionSceneManager::ls(void)
{
  unsigned int i = 0;
  for (auto region : regions) {
      std::cout << "REGION " << i << "\n";
      region->ls();
      ++i;
  }
}


double
RegionSceneManager::get_infinity(void) const
{
  return infinity;
}


int
RegionSceneManager::get_num_regions(void) const
{
  return regions.size();
}


SceneRegion *
RegionSceneManager::get_region(int index) const
{
  auto it = regions.begin();
  std::advance(it, index);
  return *it;
}
