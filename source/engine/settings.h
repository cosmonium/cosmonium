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

  bool use_depth_scaling;
  bool use_inv_scaling;
  bool use_log_scaling;
  bool camera_at_origin;
  double scale;
  bool offset_body_center;
  double min_body_size;
  double lowest_app_magnitude;
};

extern Settings settings;

#endif
