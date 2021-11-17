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

#ifndef QUADTREENODECOLLECTION_H
#define QUADTREENODECOLLECTION_H

#include "pandabase.h"
#include "luse.h"

class QuadTreeNode;

class QuadTreeNodeCollection
{
PUBLISHED:
    QuadTreeNodeCollection(void);
    QuadTreeNodeCollection(const QuadTreeNodeCollection &copy);
    void operator =(const QuadTreeNodeCollection &copy);
    virtual ~QuadTreeNodeCollection(void);

    void add(QuadTreeNode *node);

    INLINE size_t size(void) const { return collection.size(); }

    INLINE QuadTreeNode *operator[](size_t index) const { return collection[index]; }

    int get_num_nodes() const { return collection.size(); }

    QuadTreeNode *get_node(size_t index) const { return collection[index]; }

    MAKE_SEQ(get_nodes, get_num_nodes, get_node);

    void sort_by_distance(void);

protected:
    PTA(PT(QuadTreeNode)) collection;
};

#endif //QUADTREENODECOLLECTION_H

