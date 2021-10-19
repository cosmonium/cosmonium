/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2021 Laurent Deru.
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

#include "anchorTraverser.h"
#include "anchors.h"
#include "octreeNode.h"
#include "observer.h"
#include "infiniteFrustum.h"
#include "astro.h"
#include "dcast.h"

AnchorTraverser::~AnchorTraverser(void)
{
}
void
AnchorTraverser::traverse_anchor(AnchorBase *anchor)
{
}

bool
AnchorTraverser::enter_system(SystemAnchor *anchor)
{
  return false;
}

void
AnchorTraverser::traverse_system(SystemAnchor *anchor)
{
}

bool
AnchorTraverser::enter_octree_node(OctreeNode *anchor)
{
  return false;
}

size_t
AnchorTraverserCollector::get_num_collected(void) const
{
  return collected.size();
}

AnchorBase *
AnchorTraverserCollector::get_collected_at(int index) const
{
  return collected[index];
}


void
AnchorTraverser::traverse_octree_node(OctreeNode *anchor, std::vector<PT(AnchorBase)> &leaves)
{
}

UpdateTraverser::UpdateTraverser(double time, Observer &observer, double limit, unsigned long int update_id):
    time(time),
    observer(observer),
    limit(limit),
    update_id(update_id)
{
}

void
UpdateTraverser::traverse_anchor(AnchorBase *anchor)
{
    anchor->update_and_update_observer(time, observer, update_id);
    anchor->update_id = update_id;
    if (anchor->visible || anchor->visibility_override) {
        collected.push_back(anchor);
    }
}

bool
UpdateTraverser::enter_system(SystemAnchor *anchor)
{
    traverse_anchor(anchor);
    return ((anchor->visible || anchor->visibility_override) && anchor->resolved) || anchor->force_update;
}

void
UpdateTraverser::traverse_system(SystemAnchor *anchor)
{
  for(auto child : anchor->children) {
    child->traverse(*this);
  }
}

bool
UpdateTraverser::enter_octree_node(OctreeNode *octree_node)
{
    //TODO: Octree root must be separate from octree node. Use enter_system ?
    double distance = (octree_node->center - observer.frustum->get_position()).length() - octree_node->radius;
    if (distance <= 0.0) {
        return true;
    }
    if (abs_to_app_mag(octree_node->max_magnitude, distance) > limit) {
        return false;
    }
    return observer.frustum->is_sphere_in(octree_node->center, octree_node->radius);
}

void
UpdateTraverser::traverse_octree_node(OctreeNode *octree_node, std::vector<PT(AnchorBase)> &leaves)
{
    LPoint3d frustum_position = observer.frustum->get_position();
    double distance = (octree_node->center - frustum_position).length() - octree_node->radius;
    double faintest;
    if (distance > 0.0) {
        faintest = app_to_abs_mag(limit, distance);
    } else {
        faintest = 99.0;
    }
    for (auto leaf : leaves) {
        double abs_magnitude = leaf->get_absolute_magnitude();
        bool traverse = false;
        if (abs_magnitude < faintest) {
            LVector3d direction = leaf->get_absolute_position() - frustum_position;
            distance = direction.length();
            if (distance > 0.0) {
                double app_magnitude = abs_to_app_mag(abs_magnitude, distance);
                if (app_magnitude < limit) {
                    traverse = observer.frustum->is_sphere_in(leaf->get_absolute_position(), leaf->_extend);
                }
            } else {
                traverse = true;
            }
        }
        if (traverse) {
            leaf->traverse(*this);
        }
    }
}

FindClosestSystemTraverser::FindClosestSystemTraverser(Observer &observer, AnchorBase *system, double distance) :
    observer(observer),
    system(system),
    distance(distance)
{
}

AnchorBase *
FindClosestSystemTraverser::get_closest_system(void)
{
  return system;
}

void
FindClosestSystemTraverser::traverse_anchor(AnchorBase *anchor)
{
}

bool
FindClosestSystemTraverser::enter_system(SystemAnchor *anchor)
{
  return false;
}

void
FindClosestSystemTraverser::traverse_system(SystemAnchor *anchor)
{
}

bool
FindClosestSystemTraverser::enter_octree_node(OctreeNode *octree_node)
{
  //TODO: Check node content ?
  double octree_min_distance = (octree_node->center - observer.get_absolute_position()).length() - octree_node->radius;
  return octree_min_distance <= distance;
}

void
FindClosestSystemTraverser::traverse_octree_node(OctreeNode *octree_node, std::vector<PT(AnchorBase)> &leaves)
{
  for (auto leaf : leaves) {
    LPoint3d global_delta = leaf->get_absolute_reference_point() - observer.get_absolute_reference_point();
    LPoint3d local_delta = leaf->get_local_position() - observer.get_local_position();
    double leaf_distance = (global_delta + local_delta).length();
    if (leaf_distance < distance) {
      distance = leaf_distance;
      system = leaf;
    }
  }
}
FindLightSourceTraverser::FindLightSourceTraverser(double limit, LPoint3d position) :
    limit(limit),
    position(position)
{
}

void
FindLightSourceTraverser::traverse_anchor(AnchorBase *anchor)
{
  collected.push_back(anchor);
}

bool
FindLightSourceTraverser::enter_system(SystemAnchor *anchor)
{
  //TODO: Is absolute reference point delta accurate enough ?
  LPoint3d global_delta = anchor->get_absolute_reference_point() - position;
  double distance = (global_delta).length();
  return (anchor->content & AnchorBase::Emissive) != 0 && (distance == 0 || abs_to_app_mag(anchor->_abs_magnitude, distance) < limit);
}

void
FindLightSourceTraverser::traverse_system(SystemAnchor *anchor)
{
  for (auto child : anchor->children) {
    if ((child->content & AnchorBase::Emissive) == 0) {
      continue;
    }
    //TODO: Is global position accurate enough ?
    LPoint3d global_delta = child->get_absolute_reference_point() - position;
    double distance = (global_delta).length();
    if (distance == 0 || abs_to_app_mag(child->_abs_magnitude, distance) < limit) {
        child->traverse(*this);
    }
  }
}

bool
FindLightSourceTraverser::enter_octree_node(OctreeNode *octree_node)
{
  //TODO: Check node content ?
  double distance = (octree_node->center - position).length() - octree_node->radius;
  if (distance <= 0.0) {
    return true;
  }
  if (abs_to_app_mag(octree_node->max_magnitude, distance) > limit) {
      return false;
  }
  return true;
}

void
FindLightSourceTraverser::traverse_octree_node(OctreeNode *octree_node, std::vector<PT(AnchorBase)> &leaves)
{
  double distance = (octree_node->center - position).length() - octree_node->radius;
  double faintest;
  if (distance > 0.0) {
    faintest = app_to_abs_mag(limit, distance);
  } else {
    faintest = 99.0;
  }
  for (auto leaf : leaves) {
    double abs_magnitude = leaf->_abs_magnitude;
    if (abs_magnitude < faintest) {
      distance = (leaf->get_absolute_reference_point() - position).length();
      if (distance > 0.0) {
        double app_magnitude = abs_to_app_mag(abs_magnitude, distance);
        if (app_magnitude < limit) {
          leaf->traverse(*this);
        }
      } else {
        leaf->traverse(*this);
      }
    }
  }
}

void
FindObjectsInVisibleResolvedSystemsTraverser::traverse_anchor(AnchorBase *anchor)
{
  collected.push_back(anchor);
}

bool
FindObjectsInVisibleResolvedSystemsTraverser::enter_system(SystemAnchor *anchor)
{
  collected.push_back(anchor);
  return anchor->visible and anchor->resolved;
}

void
FindObjectsInVisibleResolvedSystemsTraverser::traverse_system(SystemAnchor *anchor)
{
  for (auto child : anchor->children) {
    child->traverse(*this);
  }
}

bool
FindObjectsInVisibleResolvedSystemsTraverser::enter_octree_node(OctreeNode *octree_node)
{
  return false;
}

void
FindObjectsInVisibleResolvedSystemsTraverser::traverse_octree_node(OctreeNode *octree_node, std::vector<PT(AnchorBase)> &leaves)
{
}

FindShadowCastersTraverser::FindShadowCastersTraverser(AnchorBase *target, LVector3d vector_to_light_source, double distance_to_light_source, double light_source_radius) :
  target(target),
  vector_to_light_source(vector_to_light_source),
  distance_to_light_source(distance_to_light_source),
  parent_systems()
{
  body_position = target->get_local_position();
  body_bounding_radius = target->_extend;
  light_source_angular_radius = asin(light_source_radius / (distance_to_light_source - body_bounding_radius));
  AnchorTreeBase *parent = target->parent;
  while (parent->content != ~0) {
    parent_systems.push_back(DCAST(AnchorBase, parent));
    parent = parent->parent;
  }
}

bool
FindShadowCastersTraverser::check_cast_shadow(AnchorBase *occluder)
{
  bool cast_shadow = false;
  LPoint3d occluder_position = occluder->get_local_position();
  double occluder_bounding_radius = occluder->_extend;
  LPoint3d relative_position = occluder_position - body_position;
  double t = vector_to_light_source.dot(relative_position);
  if (t >= 0 && t <= distance_to_light_source) {
    double distance = relative_position.length() - body_bounding_radius;
    double occluder_angular_radius;
    if (occluder_bounding_radius < distance) {
      occluder_angular_radius = asin(occluder_bounding_radius / distance);
    } else {
      occluder_angular_radius = M_PI / 2;
    }
    double ar_ratio = occluder_angular_radius / light_source_angular_radius;
    //TODO: No longer valid if we are using HDR
    //If the shadow coef is smaller than the min change in pixel color
    //the umbra will have no visible impact
    if (ar_ratio * ar_ratio > 1.0 / 255) {
      double distance_to_projection = (relative_position - vector_to_light_source * t).length();
      double penumbra_radius = (1 + ar_ratio) * occluder_bounding_radius;
      //TODO: Should check also the visible size of the penumbra
      if (distance_to_projection < penumbra_radius + body_bounding_radius) {
        cast_shadow = true;
      }
    }
  }
  return cast_shadow;
}

void
FindShadowCastersTraverser::traverse_anchor(AnchorBase *anchor)
{
  if (anchor != target && (anchor->content & AnchorBase::Reflective) != 0 && check_cast_shadow(anchor)) {
    collected.push_back(anchor);
  }
}

bool
FindShadowCastersTraverser::enter_system(SystemAnchor *anchor)
{
  auto it = find(parent_systems.begin(), parent_systems.end(), anchor);
  bool enter = (it != parent_systems.end()) || ((anchor->content & AnchorBase::Reflective) != 0 && check_cast_shadow(anchor));
  //TODO: We should trigger update here if needed (using update_id) instead of deferring update to next frame
  anchor->force_update = enter;
  return enter;
}

void
FindShadowCastersTraverser::traverse_system(SystemAnchor *anchor)
{
  for (auto child : anchor->children) {
    child->traverse(*this);
  }
}

bool
FindShadowCastersTraverser::enter_octree_node(OctreeNode *octree_node)
{
  return false;
}

void
FindShadowCastersTraverser::traverse_octree_node(OctreeNode *octree_node, std::vector<PT(AnchorBase)> &leaves)
{
}
