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

#ifndef COLLISIONENTRIESCOLLECTION_H
#define COLLISIONENTRIESCOLLECTION_H

#include "referenceCount.h"
#include "pandabase.h"
#include "luse.h"
#include <vector>


class CollisionEntry;
class CollisionHandlerQueue;

class CollisionEntriesCollection : public ReferenceCount
{
PUBLISHED:
  virtual ~CollisionEntriesCollection(void);

  size_t get_num_entries(void) const;
  CollisionEntry *get_entry(int index) const;

  MAKE_SEQ(get_entries, get_num_entries, get_entry);
  MAKE_SEQ_PROPERTY(entries, get_num_entries, get_entry);

public:
  void add_entries(CollisionHandlerQueue *queue);

protected:
  std::vector<PT(CollisionEntry)> entries;
};

#endif
