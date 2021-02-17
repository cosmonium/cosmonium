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

#ifndef ANCHORTRAVERSER_H
#define ANCHORTRAVERSER_H

#include "referenceCount.h"
#include "pandabase.h"
#include "luse.h"
#include <vector>

class AnchorBase;
class SystemAnchor;
class OctreeNode;
class Observer;

class AnchorTraverser : public ReferenceCount
{
PUBLISHED:
  virtual ~AnchorTraverser(void);

  virtual void traverse_anchor(AnchorBase *anchor);

  virtual bool enter_system(SystemAnchor *anchor);

  virtual void traverse_system(SystemAnchor *anchor);

  virtual bool enter_octree_node(OctreeNode *octree_node);

  virtual void traverse_octree_node(OctreeNode *octree_node, std::vector<PT(AnchorBase)> &leaves);
};

class AnchorTraverserCollector : public AnchorTraverser
{
PUBLISHED:
  size_t get_num_collected(void) const;
  AnchorBase *get_collected_at(int index) const;

  MAKE_SEQ(get_collected, get_num_collected, get_collected_at);

protected:
  std::vector<PT(AnchorBase)> collected;
};

class UpdateTraverser : public AnchorTraverserCollector
{
PUBLISHED:
  UpdateTraverser(double time, Observer &observer, double limit);

  virtual void traverse_anchor(AnchorBase *anchor);

  virtual bool enter_system(SystemAnchor *anchor);

  virtual void traverse_system(SystemAnchor *anchor);

  virtual bool enter_octree_node(OctreeNode *octree_node);

  virtual void traverse_octree_node(OctreeNode *octree_node, std::vector<PT(AnchorBase)> &leaves);

protected:
  double time;
  Observer &observer;
  double limit;
};

class FindClosestSystemTraverser : public AnchorTraverser
{
PUBLISHED:
  FindClosestSystemTraverser(Observer &observer, AnchorBase *system = 0, double distance = 0);

  AnchorBase *get_closest_system(void);
  MAKE_PROPERTY(closest_system, get_closest_system);

  virtual void traverse_anchor(AnchorBase *anchor);

  virtual bool enter_system(SystemAnchor *anchor);

  virtual void traverse_system(SystemAnchor *anchor);

  virtual bool enter_octree_node(OctreeNode *octree_node);

  virtual void traverse_octree_node(OctreeNode *octree_node, std::vector<PT(AnchorBase)> &leaves);

protected:
  Observer &observer;
  PT(AnchorBase) system;
  double distance;
};

class FindLightSourceTraverser : public AnchorTraverserCollector
{
PUBLISHED:
  FindLightSourceTraverser(double limit, LPoint3d position);

  virtual void traverse_anchor(AnchorBase *anchor);

  virtual bool enter_system(SystemAnchor *anchor);

  virtual void traverse_system(SystemAnchor *anchor);

  virtual bool enter_octree_node(OctreeNode *octree_node);

  virtual void traverse_octree_node(OctreeNode *octree_node, std::vector<PT(AnchorBase)> &leaves);

protected:
  double limit;
  LPoint3d position;
};

class FindObjectsInVisibleResolvedSystemsTraverser : public AnchorTraverserCollector
{
PUBLISHED:
  virtual void traverse_anchor(AnchorBase *anchor);

  virtual bool enter_system(SystemAnchor *anchor);

  virtual void traverse_system(SystemAnchor *anchor);

  virtual bool enter_octree_node(OctreeNode *octree_node);

  virtual void traverse_octree_node(OctreeNode *octree_node, std::vector<PT(AnchorBase)> &leaves);
};

class FindShadowCastersTraverser : public AnchorTraverserCollector
{
PUBLISHED:
  FindShadowCastersTraverser(AnchorBase *target, LVector3d vector_to_light_source, double distance_to_light_source, double light_source_radius);

  bool check_cast_shadow(AnchorBase *anchor);

  virtual void traverse_anchor(AnchorBase *anchor);

  virtual bool enter_system(SystemAnchor *anchor);

  virtual void traverse_system(SystemAnchor *anchor);

  virtual bool enter_octree_node(OctreeNode *octree_node);

  virtual void traverse_octree_node(OctreeNode *octree_node, std::vector<PT(AnchorBase)> &leaves);

protected:
  AnchorBase *target;
  LPoint3d body_position;
  double body_bounding_radius;
  LVector3d vector_to_light_source;
  double distance_to_light_source;
  double light_source_angular_radius;
  std::vector<AnchorBase *> parent_systems;
};

#endif
