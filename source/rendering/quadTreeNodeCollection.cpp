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
#include "quadTreeNodeCollection.h"
#include <algorithm>


QuadTreeNodeCollection::QuadTreeNodeCollection(void)
{
}

QuadTreeNodeCollection::
QuadTreeNodeCollection(const QuadTreeNodeCollection &copy) :
  collection(copy.collection)
{
}

void QuadTreeNodeCollection::
operator =(const QuadTreeNodeCollection &copy) {
  collection = copy.collection;
}

QuadTreeNodeCollection::~QuadTreeNodeCollection(void)
{
}

void
QuadTreeNodeCollection::add(QuadTreeNode *node)
{
  collection.push_back(node);
}

static inline bool
cmp_by_distance(QuadTreeNode *a, QuadTreeNode *b)
{
  return a->distance < b->distance;
}

void
QuadTreeNodeCollection::sort_by_distance(void)
{
  std::sort(collection.begin(), collection.end(), cmp_by_distance);
}
