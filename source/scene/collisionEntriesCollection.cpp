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


#include "collisionEntriesCollection.h"
#include "collisionHandlerQueue.h"


CollisionEntriesCollection::~CollisionEntriesCollection(void)
{
}


void
CollisionEntriesCollection::add_entries(CollisionHandlerQueue *queue)
{
  for (int i = 0; i < queue->get_num_entries(); ++i) {
    entries.push_back(queue->get_entry(i));
  }
}


size_t
CollisionEntriesCollection::get_num_entries(void) const
{
  return entries.size();
}


CollisionEntry *
CollisionEntriesCollection::get_entry(int index) const
{
  return entries[index];
}
