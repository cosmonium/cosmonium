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


#include "astro.h"
#include "haloPointsSetShape.h"
#include "scale.h"
#include "sceneAnchor.h"
#include "settings.h"
#include "stellarAnchor.h"


TypeHandle HaloPointsSetShape::_type_handle;


HaloPointsSetShape::HaloPointsSetShape(bool has_size, bool has_oid, double screen_scale) :
    PointsSetShape(has_size, has_oid, screen_scale)
{
}


HaloPointsSetShape::~HaloPointsSetShape(void)
{
}


void
HaloPointsSetShape::add_object(SceneAnchor *scene_anchor)
{
  Settings *settings = Settings::get_global_ptr();
  StellarAnchor *anchor = DCAST(StellarAnchor, scene_anchor->get_anchor());
  double app_magnitude = radiance_to_mag(anchor->_point_radiance);
  if (anchor->visible_size < settings->min_body_size * 2 && app_magnitude < settings->smallest_glare_mag && scene_anchor->get_instance() != nullptr) {
    LColor point_color = anchor->point_color;
    double coef = settings->smallest_glare_mag - app_magnitude + 6.0;
    double radius = std::max(1.0, anchor->visible_size);
    double size = radius * coef * 4.0;
    add_point(scene_anchor->scene_position, point_color, size * screen_scale, scene_anchor->get_oid_color());
  }
}
