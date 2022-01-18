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

#pragma once

float
srgb_to_linear(float color)
{
    if (color > 0.0404482362771082) {
        return pow(((color + 0.055) / 1.055), 2.4);
    } else {
        return color / 12.92;
    }
}

float
linear_to_srgb(float value)
{
    if(value > 0.0031308) {
        return 1.055 * pow(value, 0.41666) - 0.055;
    } else {
        return 12.92 * value;
    }
}

vec3
srgb_to_linear(vec3 color)
{
    return vec3(srgb_to_linear(color.r),
        srgb_to_linear(color.g),
        srgb_to_linear(color.b));
}

vec4
srgb_to_linear(in vec4 color)
{
    return vec4(srgb_to_linear(color.r),
        srgb_to_linear(color.g),
        srgb_to_linear(color.b),
        color.a);
}

vec3
linear_to_srgb(vec3 color)
{
    return vec3(linear_to_srgb(color.r),
        linear_to_srgb(color.g),
        linear_to_srgb(color.b));
}

vec4
linear_to_srgb(vec4 color)
{
    return vec4(linear_to_srgb(color.r),
        linear_to_srgb(color.g),
        linear_to_srgb(color.b),
        color.a);
}
