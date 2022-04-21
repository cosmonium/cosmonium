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

#ifndef POINTSSETSHAPE_H
#define POINTSSETSHAPE_H

#include "pandabase.h"
#include "luse.h"
#include "referenceCount.h"
#include "nodePath.h"
#include"type_utils.h"

class Geom;
class GeomNode;
class GeomPoints;
class GeomVertexWriter;
class PointConfigurator;
class SceneAnchor;
class SceneAnchorCollection;
class SceneManager;


class PointsSetShape : public TypedObject, public ReferenceCount
{
PUBLISHED:
  PointsSetShape(bool has_size, bool has_oid);

  virtual ~PointsSetShape(void);

  void make_geom(void);

  void reset(void);

  void configure(SceneManager *scene_manager, PointConfigurator *configurator);

  void reconfigure(SceneManager *scene_manager, PointConfigurator *configurator);

  void add_point(LPoint3d point, LColor color, double size, LColor oid);

  virtual void add_object(SceneAnchor *scene_anchor) = 0;

  void add_objects(SceneManager *scene_manager, SceneAnchorCollection *scene_anchors);

  NodePath get_instance(void);
  MAKE_PROPERTY(instance, get_instance);

protected:
  void create_writers(void);

protected:
  bool has_size;
  bool has_oid;
  PT(GeomNode) gnode;
  NodePath instance;
  PT(Geom) geom;
  PT(GeomPoints) geom_points;
  PT(GeomVertexData) vdata;
  unsigned int index;
  GeomVertexWriter *vwriter;
  GeomVertexWriter *colorwriter;
  GeomVertexWriter *sizewriter;
  GeomVertexWriter *oidwriter;

public:
  MAKE_TYPE_2("PointsSetShape", TypedObject, ReferenceCount);
};

#endif
