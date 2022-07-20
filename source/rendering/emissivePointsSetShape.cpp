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


#include "emissivePointsSetShape.h"
#include "scale.h"
#include "sceneAnchor.h"
#include "settings.h"
#include "stellarAnchor.h"


TypeHandle EmissivePointsSetShape::_type_handle;


EmissivePointsSetShape::EmissivePointsSetShape(bool has_size, bool has_oid, double screen_scale) :
    PointsSetShape(has_size, has_oid, screen_scale)
{
}


EmissivePointsSetShape::~EmissivePointsSetShape(void)
{
}


void
EmissivePointsSetShape::add_object(SceneAnchor *scene_anchor)
{
  Settings *settings = Settings::get_global_ptr();
  StellarAnchor *anchor = DCAST(StellarAnchor, scene_anchor->get_anchor());
  if (anchor->visible_size < settings->min_body_size * 2 && scene_anchor->get_instance() != nullptr) {
    double app_magnitude = anchor->_app_magnitude;
    LColor point_color = anchor->point_color;
    double scale = mag_to_scale(app_magnitude);
    if (scale > 0) {
      LColor color = point_color * scale;
      double size = std::max(settings->min_point_size,
                             settings->min_point_size + scale * settings->mag_pixel_scale);
      add_point(scene_anchor->scene_position, color, size * screen_scale, scene_anchor->get_oid_color());
    }
  }
}
