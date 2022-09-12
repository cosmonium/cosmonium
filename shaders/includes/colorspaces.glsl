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

vec3
linear_to_xyz(vec3 linear)
{
  const mat3 RGB2XYZ = mat3(0.4124, 0.2126, 0.0193,
                            0.3576, 0.7152, 0.1192,
                            0.1805, 0.0722, 0.9505);
  return RGB2XYZ * linear;
}

vec3
xyz_to_linear(vec3 xyz)
{
  const mat3 XYZ2RGB = mat3( 3.2405, -0.9693,  0.0556,
                            -1.5371,  1.8760, -0.2040,
                            -0.4985,  0.0416,  1.0572);
  return XYZ2RGB * xyz;
}

vec3
xyz_to_xyy(vec3 xyz)
{
  vec3 xyy;
  xyy.z = xyz.y;
  float temp = dot(vec3(1.0), xyz);
  xyy.xy = xyz.xy / temp;
  return xyy;
}

vec3
xyy_to_xyz(vec3 xyy)
{
  vec3 xyz;
  xyz.x = xyy.z * xyy.x / xyy.y;
  xyz.y = xyy.z;
  xyz.z = xyy.z * (1.0 - xyy.x - xyy.y) / xyy.y;
  return xyz;
}

vec3
linear_to_xyy(vec3 linear)
{
  return xyz_to_xyy(linear_to_xyz(linear));
}


vec3
xyy_to_linear(vec3 xyy)
{
  return xyz_to_linear(xyy_to_xyz(xyy));
}
