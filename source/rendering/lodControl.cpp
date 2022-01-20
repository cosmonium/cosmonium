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

#include "quadTreeNode.h"
#include "lodControl.h"


LodControl::~LodControl(void)
{
}

void
LodControl::set_texture_size(unsigned int texture_size)
{
}

bool
LodControl::should_instanciate(QuadTreeNode *patch, double apparent_patch_size, double distance)
{
  return patch->visible && patch->children.size() == 0;
}

bool
LodControl::should_remove(QuadTreeNode *patch, double apparent_patch_size, double distance)
{
  return !patch->visible;
}

TextureLodControl::TextureLodControl(unsigned int min_density, unsigned int density, unsigned int max_lod) :
    min_density(min_density),
    density(density),
    max_lod(max_lod),
    texture_size(0)
{
}

void
TextureLodControl::set_texture_size(unsigned int texture_size)
{
  this->texture_size = texture_size;
}

unsigned int
TextureLodControl::get_density_for(unsigned int lod)
{
  return max(min_density, density / (1 << lod));
}

bool
TextureLodControl::should_split(QuadTreeNode *patch, double apparent_patch_size, double distance)
{
  if (patch->lod < max_lod) {
    return (texture_size > 0 && apparent_patch_size > texture_size * 1.1); //TODO: add appearance.texture.can_split(patch)
  } else {
    return false;
  }

}

bool
TextureLodControl::should_merge(QuadTreeNode *patch, double apparent_patch_size, double distance)
{
  return (apparent_patch_size < texture_size / 1.1);
}

TextureOrVertexSizeLodControl::TextureOrVertexSizeLodControl(unsigned int max_vertex_size, unsigned int min_density, unsigned int density, unsigned int max_lod) :
    TextureLodControl(min_density, density, max_lod),
    max_vertex_size(max_vertex_size)
{
}

bool
TextureOrVertexSizeLodControl::should_split(QuadTreeNode *patch, double apparent_patch_size, double distance)
{
  if (patch->lod < max_lod) {
    if (texture_size > 0) {
        return apparent_patch_size > texture_size * 1.1;
    } else {
        double apparent_vertex_size = apparent_patch_size / patch->density;
        return apparent_vertex_size > max_vertex_size;
    }
  } else {
    return false;
  }
}

bool
TextureOrVertexSizeLodControl::should_merge(QuadTreeNode *patch, double apparent_patch_size, double distance)
{
  if (texture_size > 0) {
      return apparent_patch_size < texture_size / 1.1;
  } else {
      double apparent_vertex_size = apparent_patch_size / patch->density;
      return apparent_vertex_size < max_vertex_size / 1.1;
  }
}

VertexSizeLodControl::VertexSizeLodControl(unsigned int max_vertex_size, unsigned int density, unsigned int max_lod) :
    density(density),
    max_lod(max_lod),
    max_vertex_size(max_vertex_size)
{
}

unsigned int
VertexSizeLodControl::get_density_for(unsigned int lod)
{
  return density;
}

bool
VertexSizeLodControl::should_split(QuadTreeNode *patch, double apparent_patch_size, double distance)
{
  if (patch->lod < max_lod) {
      double apparent_vertex_size = apparent_patch_size / patch->density;
      return apparent_vertex_size > max_vertex_size * 1.1;
  } else {
      return false;
  }
}

bool
VertexSizeLodControl::should_merge(QuadTreeNode *patch, double apparent_patch_size, double distance)
{
    double apparent_vertex_size = apparent_patch_size / patch->density;
    return apparent_vertex_size < max_vertex_size / 1.1;
}

VertexSizeMaxDistanceLodControl::VertexSizeMaxDistanceLodControl(double max_distance, unsigned int max_vertex_size, unsigned int density, unsigned int max_lod) :
    VertexSizeLodControl(max_vertex_size, density, max_lod),
    max_distance(max_distance)
{
}

bool
VertexSizeMaxDistanceLodControl::should_instanciate(QuadTreeNode *patch, double apparent_patch_size, double distance)
{
  return patch->visible && distance < max_distance;
}

bool
VertexSizeMaxDistanceLodControl::should_remove(QuadTreeNode *patch, double apparent_patch_size, double distance)
{
  return !patch->visible;
}
