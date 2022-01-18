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

#version 330

uniform ivec2 screen_size;
uniform sampler2D scene;

out vec4 result;

#pragma include "shaders/includes/colorspaces.glsl"

void main()
{
  vec2 texcoord = gl_FragCoord.xy / screen_size;
  vec3 pixel_color = textureLod(scene, texcoord, 0).xyz;
  result = vec4(linear_to_srgb(pixel_color), 1);
}
