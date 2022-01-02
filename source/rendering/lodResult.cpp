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
#include "lodResult.h"

LodResult::LodResult(void) :
  to_split(),
  to_merge(),
  to_show(),
  to_remove(),
  max_lod(0)
{
}

LodResult::~LodResult(void)
{
}

void
LodResult::add_to_split(QuadTreeNode *patch)
{
  to_split.add(patch);
}

void
LodResult::add_to_merge(QuadTreeNode *patch)
{
  to_merge.add(patch);
}

void
LodResult::add_to_show(QuadTreeNode *patch)
{
  to_show.add(patch);
}

void
LodResult::add_to_remove(QuadTreeNode *patch)
{
  to_remove.add(patch);
}

void
LodResult::check_max_lod(QuadTreeNode *patch)
{
  max_lod = max(max_lod, patch->lod);
}

void
LodResult::sort_by_distance(void)
{
  to_split.sort_by_distance();
  to_merge.sort_by_distance();
  to_show.sort_by_distance();
  to_remove.sort_by_distance();
}

