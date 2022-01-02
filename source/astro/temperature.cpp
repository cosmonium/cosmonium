/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2019 Laurent Deru.
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

#include "math.h"
#include "temperature.h"

inline double
clamp(double low, double high, double x)
{
  return std::max(low, std::min(high, x));
}

LColor
temp_to_RGB(double kelvin)
{
    double temp = kelvin / 100.0;
    double red;
    double green;
    double blue;

    if(temp <= 66) {
        red = 255;

        green = temp;
        green = 99.4708025861 * log(green) - 161.1195681661;

        if(temp <= 19) {
            blue = 0;
        } else {
            blue = temp - 10;
            blue = 138.5177312231 * log(blue) - 305.0447927307;
        }
    } else {
        red = temp - 60;
        red = 329.698727446 * pow(red, -0.1332047592);

        green = temp - 60;
        green = 288.1221695283 * pow(green, -0.0755148492 );

        blue = 255;
    }
    return LColor(clamp(0, 1, red/255.0), clamp(0, 1, green/255.0), clamp(0, 1, blue/255.0), 1.0);
}
