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

#ifndef SETTINGS_H
#define SETTINGS_H

#include "pandabase.h"
#include "luse.h"

class Settings
{
public:
  Settings(void) {}

protected:
  Settings(Settings const &other);

PUBLISHED:
  static Settings * get_global_ptr(void);

  bool offset_body_center;
  bool camera_at_origin;
  bool use_depth_scaling;
  bool use_inv_scaling;
  bool use_log_scaling;

  bool inverse_z;
  double default_near_plane;
  bool infinite_far_plane;
  double default_far_plane;
  double infinite_plane;
  bool auto_infinite_plane;
  double lens_far_limit;

  double min_body_size;
  double min_point_size;
  double min_mag_scale;
  double mag_pixel_scale;
  double lowest_app_magnitude;
  double max_app_magnitude;
  double smallest_glare_mag;

  int mouse_click_collision_bit;
};

extern Settings settings;

#endif
