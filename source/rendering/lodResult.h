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

#ifndef LODRESULT_H
#define LODRESULT_H

#include "pandabase.h"
#include "referenceCount.h"
#include "quadTreeNodeCollection.h"

class QuadTreeNode;

class LodResult : public ReferenceCount
{
PUBLISHED:
    LodResult(void);

    virtual ~LodResult(void);

    void add_to_split(QuadTreeNode *patch);

    void add_to_merge(QuadTreeNode *patch);

    void add_to_show(QuadTreeNode *patch);

    void add_to_remove(QuadTreeNode *patch);

    void check_max_lod(QuadTreeNode *patch);

    void sort_by_distance(void);

    QuadTreeNodeCollection to_split;
    QuadTreeNodeCollection to_merge;
    QuadTreeNodeCollection to_show;
    QuadTreeNodeCollection to_remove;
    int max_lod;
};

#endif //LODRESULT_H

