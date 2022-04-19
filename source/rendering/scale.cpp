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


#include "scale.h"
#include "settings.h"

double
mag_to_scale(double magnitude)
{
  Settings *settings = Settings::get_global_ptr();
  if (magnitude > settings->lowest_app_magnitude) {
    return 0.0;
  } else if (magnitude < settings->max_app_magnitude) {
    return 1.0;
  } else {
    return settings->min_mag_scale + (1 - settings->min_mag_scale) * (settings->lowest_app_magnitude - magnitude) / (settings->lowest_app_magnitude - settings->max_app_magnitude);
  }
}
