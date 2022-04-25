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


#include "pointsSetShape.h"

#include "geom.h"
#include "geomNode.h"
#include "geomPoints.h"
#include "geomVertexWriter.h"
//#include "pointConfigurator.h"
#include "sceneAnchor.h"
#include "sceneAnchorCollection.h"
#include "sceneManager.h"


TypeHandle PointsSetShape::_type_handle;


PointsSetShape::PointsSetShape(bool has_size, bool has_oid) :
  has_size(has_size),
  has_oid(has_oid),
  gnode(new GeomNode("starfield")),
  instance(gnode),
  index(0),
  vwriter(nullptr),
  colorwriter(nullptr),
  sizewriter(nullptr),
  oidwriter(nullptr)
{
}


PointsSetShape::~PointsSetShape(void)
{
  delete vwriter;
  delete colorwriter;
  delete sizewriter;
  delete oidwriter;
}


void
PointsSetShape::make_geom(void)
{
  PT(GeomVertexArrayFormat) array = new GeomVertexArrayFormat();
  array->add_column(InternalName::get_vertex(), 3, Geom::NT_float32, Geom::C_point);
  array->add_column(InternalName::get_color(), 4, Geom::NT_float32, Geom::C_color);
  if (has_size) {
    array->add_column(InternalName::get_size(), 1, Geom::NT_float32, Geom::C_other);
  }
  if (has_oid) {
    PT(InternalName) oids_column_name = InternalName::make("oid");
    array->add_column(oids_column_name, 4, Geom::NT_float32, Geom::C_other);
  }
  PT(GeomVertexFormat) source_format = new GeomVertexFormat();
  source_format->add_array(array);
  CPT(GeomVertexFormat) vertex_format = GeomVertexFormat::register_format(source_format);
  vdata = new GeomVertexData("vdata", vertex_format, Geom::UH_stream);
  geom_points = new GeomPoints(Geom::UH_stream);
  geom = new Geom(vdata);
  geom->add_primitive(geom_points);
}


void
PointsSetShape::reset(void)
{
  gnode->remove_all_geoms();
  make_geom();
  gnode->add_geom(geom);
  index = 0;
}

void
PointsSetShape::create_writers(void)
{
  delete vwriter;
  delete colorwriter;
  delete sizewriter;
  delete oidwriter;
  vwriter = new GeomVertexWriter(vdata, InternalName::get_vertex());
  colorwriter = new GeomVertexWriter(vdata, InternalName::get_color());
  if (has_size) {
    sizewriter = new GeomVertexWriter(vdata, InternalName::get_size());
  }
  if (has_oid) {
    PT(InternalName) oids_column_name = InternalName::make("oid");
    oidwriter = new GeomVertexWriter(vdata, oids_column_name);
  }
}

void
PointsSetShape::configure(SceneManager *scene_manager, PointConfigurator *configurator)
{
}


void
PointsSetShape::reconfigure(SceneManager *scene_manager, PointConfigurator *configurator)
{
}


void
PointsSetShape::add_point(LPoint3d point, LColor color, double size, LColor oid)
{
  vwriter->set_data3(LCAST(PN_stdfloat, point));
  colorwriter->set_data4(color);
  if (has_size) {
      sizewriter->set_data1(size);
  }
  if (has_oid) {
      oidwriter->set_data4(oid);
  }
  geom_points->add_vertex(index);
  index += 1;
}


void
PointsSetShape::add_objects(SceneManager *scene_manager, SceneAnchorCollection *scene_anchors)
{
  vdata->set_num_rows(scene_anchors->get_num_scene_anchors());
  geom_points->reserve_num_vertices(scene_anchors->get_num_scene_anchors());
  create_writers();
  for (unsigned int i = 0; i < scene_anchors->get_num_scene_anchors(); ++i) {
    add_object(scene_anchors->get_scene_anchor(i));
  }
}

NodePath
PointsSetShape::get_instance(void)
{
  return instance;
}
