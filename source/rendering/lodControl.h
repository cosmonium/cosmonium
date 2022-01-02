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

#ifndef LODCONTROL_H
#define LODCONTROL_H

#include "pandabase.h"
#include "referenceCount.h"

class QuadTreeNode;

class LodControl : public ReferenceCount
{
PUBLISHED:
    virtual ~LodControl(void);

    virtual unsigned int get_density_for(unsigned int lod) = 0;

    virtual void set_texture_size(unsigned int texture_size);

    virtual bool should_split(QuadTreeNode *patch, double apparent_patch_size, double distance) = 0;

    virtual bool should_merge(QuadTreeNode *patch, double apparent_patch_size, double distance) = 0;

    virtual bool should_instanciate(QuadTreeNode *patch, double apparent_patch_size, double distance);

    virtual bool should_remove(QuadTreeNode *patch, double apparent_patch_size, double distance);
};

class TextureLodControl : public LodControl
{
PUBLISHED:
    TextureLodControl(unsigned int min_density, unsigned int density, unsigned int max_lod=100);

    void set_texture_size(unsigned int texture_size);

    virtual unsigned int get_density_for(unsigned int lod);

    virtual bool should_split(QuadTreeNode *patch, double apparent_patch_size, double distance);

    virtual bool should_merge(QuadTreeNode *patch, double apparent_patch_size, double distance);

protected:
    unsigned int min_density;
    unsigned int density;
    unsigned int max_lod;
    unsigned int texture_size;
};

class VertexSizeLodControl : public LodControl
{
PUBLISHED:
    VertexSizeLodControl(unsigned int max_vertex_size, unsigned int density, unsigned int max_lod=100);

    virtual unsigned int get_density_for(unsigned int lod);

    virtual bool should_split(QuadTreeNode *patch, double apparent_patch_size, double distance);

    virtual bool should_merge(QuadTreeNode *patch, double apparent_patch_size, double distance);

protected:
    unsigned int density;
    unsigned int max_lod;
    unsigned int max_vertex_size;
};


class TextureOrVertexSizeLodControl : public TextureLodControl
{
PUBLISHED:
    TextureOrVertexSizeLodControl(unsigned int max_vertex_size, unsigned int min_density, unsigned int density, unsigned int max_lod=100);

    virtual bool should_split(QuadTreeNode *patch, double apparent_patch_size, double distance);

    virtual bool should_merge(QuadTreeNode *patch, double apparent_patch_size, double distance);

protected:
    unsigned int max_vertex_size;
};

class VertexSizeMaxDistanceLodControl : public VertexSizeLodControl
{
PUBLISHED:
    VertexSizeMaxDistanceLodControl(double max_distance, unsigned int max_vertex_size, unsigned int density, unsigned int max_lod=100);

    virtual bool should_instanciate(QuadTreeNode *patch, double apparent_patch_size, double distance);

    virtual bool should_remove(QuadTreeNode *patch, double apparent_patch_size, double distance);

protected:
    double max_distance;
};

#endif //LODCONTROL_H
